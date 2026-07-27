from __future__ import annotations

import logging
import time
from datetime import datetime
from threading import RLock
from typing import Any

from app.database.repositories import ReadingRepository
from app.services.reading_spool import ReadingSpool


logger = logging.getLogger("energy_monitoring.buffered_reading_repository")


class BufferedReadingRepository:
    """Small write buffer around ReadingRepository with durable spool fallback."""

    def __init__(
        self,
        repository: ReadingRepository,
        *,
        reading_spool: ReadingSpool | None = None,
        max_rows: int = 100,
        max_seconds: int = 10,
    ) -> None:
        self.repository = repository
        self.reading_spool = reading_spool
        self.max_rows = max(1, int(max_rows))
        self.max_seconds = max(1, int(max_seconds))
        self._buffer: list[dict[str, Any]] = []
        self._last_flush_monotonic = time.monotonic()
        self._lock = RLock()

    def insert_reading(
        self,
        meter_id: str,
        timestamp: datetime,
        readings: dict,
        *,
        meter_timestamp: datetime | None = None,
        collected_at: datetime | None = None,
        reading_date: str = "",
        reading_time: str = "",
        timestamp_source: str = "collector_fallback",
    ) -> bool:
        payload = {
            "meter_id": meter_id,
            "timestamp": timestamp,
            "readings": readings,
            "meter_timestamp": meter_timestamp,
            "collected_at": collected_at,
            "reading_date": reading_date,
            "reading_time": reading_time,
            "timestamp_source": timestamp_source,
        }

        with self._lock:
            self._buffer.append(payload)
            if self._should_flush_locked():
                self.flush()
        return True

    def insert_reading_immediate(
        self,
        meter_id: str,
        timestamp: datetime,
        readings: dict,
        *,
        meter_timestamp: datetime | None = None,
        collected_at: datetime | None = None,
        reading_date: str = "",
        reading_time: str = "",
        timestamp_source: str = "collector_fallback",
    ) -> bool:
        return self.repository.insert_reading(
            meter_id=meter_id,
            timestamp=timestamp,
            readings=readings,
            meter_timestamp=meter_timestamp,
            collected_at=collected_at,
            reading_date=reading_date,
            reading_time=reading_time,
            timestamp_source=timestamp_source,
        )

    def _should_flush_locked(self) -> bool:
        if len(self._buffer) >= self.max_rows:
            return True
        return time.monotonic() - self._last_flush_monotonic >= self.max_seconds

    def flush(self) -> int:
        with self._lock:
            if not self._buffer:
                return 0

            pending = list(self._buffer)
            self._buffer.clear()
            self._last_flush_monotonic = time.monotonic()

        try:
            self.repository.insert_readings(pending)
            logger.info("Flushed %s buffered reading(s) to PostgreSQL.", len(pending))
            return len(pending)
        except Exception as exc:
            logger.exception("Buffered PostgreSQL write failed for %s reading(s): %s", len(pending), exc)
            self._spool_failed_batch(pending)
            return 0

    def _spool_failed_batch(self, pending: list[dict[str, Any]]) -> None:
        if self.reading_spool is None:
            raise RuntimeError("Buffered PostgreSQL write failed and no durable reading spool is configured.")

        queued_count = 0
        for payload in pending:
            if self.reading_spool.enqueue(
                meter_id=payload["meter_id"],
                timestamp=payload["timestamp"],
                readings=payload["readings"],
                meter_timestamp=payload.get("meter_timestamp"),
                collected_at=payload.get("collected_at"),
                reading_date=payload.get("reading_date", ""),
                reading_time=payload.get("reading_time", ""),
                timestamp_source=payload.get("timestamp_source", "collector_fallback"),
            ):
                queued_count += 1

        logger.warning(
            "Queued %s/%s buffered reading(s) to durable spool after PostgreSQL write failure.",
            queued_count,
            len(pending),
        )
