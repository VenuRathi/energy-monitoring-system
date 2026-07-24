from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Mapping


logger = logging.getLogger("energy_monitoring.reading_spool")


@dataclass(frozen=True)
class QueuedReading:
    queue_id: int
    meter_id: str
    timestamp: datetime
    meter_timestamp: datetime | None
    collected_at: datetime
    reading_date: str
    reading_time: str
    timestamp_source: str
    readings: dict[str, Any]


InsertQueuedReading = Callable[[QueuedReading], bool]


class ReadingSpool:
    """Durable local queue for readings collected while PostgreSQL is unavailable."""

    def __init__(
        self,
        path: str | Path,
        *,
        max_rows: int = 100_000,
        max_rows_per_meter: int = 50_000,
        retention_days: int = 30,
    ) -> None:
        self.path = Path(path)
        self.max_rows = max(1, int(max_rows))
        self.max_rows_per_meter = max(1, int(max_rows_per_meter))
        self.retention_days = max(0, int(retention_days))
        self._lock = RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000;")
        connection.execute("PRAGMA journal_mode = WAL;")
        connection.execute("PRAGMA synchronous = NORMAL;")
        return connection

    @contextmanager
    def _managed_connection(self):
        connection = self._connect()
        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._managed_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS queued_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meter_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    timestamp_source TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    queued_at TEXT NOT NULL,
                    UNIQUE (meter_id, timestamp, timestamp_source)
                );
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_queued_readings_order
                ON queued_readings (id);
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_queued_readings_meter_order
                ON queued_readings (meter_id, id);
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS spool_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _serialize_datetime(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _set_metadata(self, connection: sqlite3.Connection, key: str, value: str) -> None:
        connection.execute(
            """
            INSERT INTO spool_metadata (key, value)
            VALUES (?, ?)
            ON CONFLICT (key) DO UPDATE SET value = excluded.value;
            """,
            (key, value),
        )

    def _purge_expired(self, connection: sqlite3.Connection, now: datetime) -> int:
        if self.retention_days <= 0:
            return 0
        cutoff = now - timedelta(days=self.retention_days)
        cursor = connection.execute(
            "DELETE FROM queued_readings WHERE queued_at < ?;",
            (cutoff.isoformat(),),
        )
        return cursor.rowcount

    def enqueue(
        self,
        *,
        meter_id: str,
        timestamp: datetime,
        readings: Mapping[str, Any],
        meter_timestamp: datetime | None = None,
        collected_at: datetime | None = None,
        reading_date: str = "",
        reading_time: str = "",
        timestamp_source: str = "collector_fallback",
    ) -> bool:
        queued_at = self._as_utc(collected_at or datetime.now(timezone.utc))
        normalized_timestamp = self._as_utc(timestamp)
        normalized_meter_timestamp = self._as_utc(meter_timestamp) if meter_timestamp is not None else None
        payload = {
            "meter_id": meter_id,
            "timestamp": self._serialize_datetime(normalized_timestamp),
            "meter_timestamp": self._serialize_datetime(normalized_meter_timestamp),
            "collected_at": self._serialize_datetime(queued_at),
            "reading_date": reading_date,
            "reading_time": reading_time,
            "timestamp_source": timestamp_source,
            "readings": dict(readings),
        }

        with self._lock, self._managed_connection() as connection:
            self._purge_expired(connection, queued_at)
            duplicate = connection.execute(
                """
                SELECT 1
                FROM queued_readings
                WHERE meter_id = ? AND timestamp = ? AND timestamp_source = ?
                LIMIT 1;
                """,
                (meter_id, normalized_timestamp.isoformat(), timestamp_source),
            ).fetchone()
            if duplicate is not None:
                return False

            total_count = int(connection.execute("SELECT COUNT(*) FROM queued_readings;").fetchone()[0])
            meter_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM queued_readings WHERE meter_id = ?;",
                    (meter_id,),
                ).fetchone()[0]
            )
            if total_count >= self.max_rows or meter_count >= self.max_rows_per_meter:
                message = (
                    f"Reading spool limit reached for meter {meter_id} "
                    f"(total={total_count}, meter={meter_count})."
                )
                self._set_metadata(connection, "last_replay_error", message)
                logger.error(message)
                return False

            connection.execute(
                """
                INSERT INTO queued_readings (
                    meter_id, timestamp, timestamp_source, payload_json, queued_at
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    meter_id,
                    normalized_timestamp.isoformat(),
                    timestamp_source,
                    json.dumps(payload, separators=(",", ":")),
                    queued_at.isoformat(),
                ),
            )
            self._set_metadata(connection, "last_enqueued_at", queued_at.isoformat())
        logger.warning("Queued reading for meter %s because PostgreSQL was unavailable.", meter_id)
        return True

    def _row_to_reading(self, row: sqlite3.Row) -> QueuedReading:
        payload = json.loads(row["payload_json"])
        timestamp = self._parse_datetime(payload.get("timestamp"))
        collected_at = self._parse_datetime(payload.get("collected_at"))
        if timestamp is None or collected_at is None:
            raise ValueError(f"Spool row {row['id']} contains an invalid timestamp.")
        return QueuedReading(
            queue_id=int(row["id"]),
            meter_id=str(payload["meter_id"]),
            timestamp=timestamp,
            meter_timestamp=self._parse_datetime(payload.get("meter_timestamp")),
            collected_at=collected_at,
            reading_date=str(payload.get("reading_date", "")),
            reading_time=str(payload.get("reading_time", "")),
            timestamp_source=str(payload.get("timestamp_source", "collector_fallback")),
            readings=dict(payload.get("readings") or {}),
        )

    def replay(self, callbacks: Mapping[str, InsertQueuedReading], *, limit: int = 500) -> dict[str, int]:
        bounded_limit = max(1, int(limit))
        replayed = 0
        duplicates = 0
        failed = 0
        failed_meter_ids: set[str] = set()
        last_error = ""

        with self._lock, self._managed_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM queued_readings ORDER BY id ASC LIMIT ?;",
                (bounded_limit,),
            ).fetchall()

            for row in rows:
                meter_id = str(row["meter_id"])
                if meter_id in failed_meter_ids:
                    continue
                callback = callbacks.get(meter_id)
                if callback is None:
                    continue
                try:
                    queued_reading = self._row_to_reading(row)
                    inserted = callback(queued_reading)
                except Exception as exc:
                    failed += 1
                    failed_meter_ids.add(meter_id)
                    last_error = f"Meter {meter_id} replay failed: {exc}"
                    logger.exception(last_error)
                    continue

                connection.execute("DELETE FROM queued_readings WHERE id = ?;", (row["id"],))
                if inserted:
                    replayed += 1
                else:
                    duplicates += 1

            replayed_total = replayed + duplicates
            if last_error:
                self._set_metadata(connection, "last_replay_error", last_error)
                self._set_metadata(connection, "last_replay_at", datetime.now(timezone.utc).isoformat())
            elif replayed_total > 0:
                self._set_metadata(connection, "last_replay_error", "")
                self._set_metadata(connection, "last_replay_at", datetime.now(timezone.utc).isoformat())

        if replayed_total:
            logger.info(
                "Replayed %s queued reading(s); discarded %s duplicate(s).",
                replayed,
                duplicates,
            )
        return {"replayed": replayed, "duplicates": duplicates, "failed": failed}

    def status(self) -> dict[str, Any]:
        with self._lock, self._managed_connection() as connection:
            self._purge_expired(connection, datetime.now(timezone.utc))
            queued_count = int(connection.execute("SELECT COUNT(*) FROM queued_readings;").fetchone()[0])
            oldest = connection.execute("SELECT MIN(queued_at) FROM queued_readings;").fetchone()[0]
            metadata = {
                row["key"]: row["value"]
                for row in connection.execute("SELECT key, value FROM spool_metadata;").fetchall()
            }
        return {
            "queuedCount": queued_count,
            "maxQueueSize": self.max_rows,
            "maxQueueSizePerMeter": self.max_rows_per_meter,
            "retentionDays": self.retention_days,
            "oldestQueuedAt": oldest or "",
            "lastReplayAt": metadata.get("last_replay_at", ""),
            "lastReplayError": metadata.get("last_replay_error", ""),
        }
