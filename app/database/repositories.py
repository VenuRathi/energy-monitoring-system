if __package__ is None or __package__ == "":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json
from contextlib import contextmanager
from datetime import date, datetime
from typing import Iterable, Sequence

from psycopg import Connection
from psycopg.rows import dict_row

from app.database.connection import get_connection
from app.database.models import ordered_parameter_columns, parameter_name_to_column_name
from config.settings import Settings


@contextmanager
def _repository_connection(
    connection: Connection | None,
    settings: Settings | None,
):
    if connection is not None:
        yield connection
        return

    if settings is None:
        raise RuntimeError("Repository requires either an open connection or runtime settings.")

    opened_connection = get_connection(settings)
    try:
        yield opened_connection
    finally:
        opened_connection.close()


class MeterRepository:
    def __init__(self, connection: Connection | None = None, settings: Settings | None = None) -> None:
        self.connection = connection
        self.settings = settings

    def upsert_meter(self, meter: dict) -> None:
        sql = """
        INSERT INTO meters (
            meter_id, meter_name, manufacturer, model, location, protocol, enabled,
            seu, driver, com_port, slave_id, baud_rate, parity, stop_bits, byte_size, timeout, one_based_map
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (meter_id)
        DO UPDATE SET
            meter_name = EXCLUDED.meter_name,
            manufacturer = EXCLUDED.manufacturer,
            model = EXCLUDED.model,
            location = EXCLUDED.location,
            protocol = EXCLUDED.protocol,
            enabled = EXCLUDED.enabled,
            seu = EXCLUDED.seu,
            driver = EXCLUDED.driver,
            com_port = EXCLUDED.com_port,
            slave_id = EXCLUDED.slave_id,
            baud_rate = EXCLUDED.baud_rate,
            parity = EXCLUDED.parity,
            stop_bits = EXCLUDED.stop_bits,
            byte_size = EXCLUDED.byte_size,
            timeout = EXCLUDED.timeout,
            one_based_map = EXCLUDED.one_based_map;
        """
        values = (
            meter["meter_id"],
            meter["meter_name"],
            meter["manufacturer"],
            meter["model"],
            meter["location"],
            meter["protocol"],
            meter.get("enabled", True),
            meter.get("seu", False),
            meter.get("driver", "schneider.pm5000"),
            meter.get("com_port", ""),
            meter.get("slave_id", 1),
            meter.get("baud_rate", 9600),
            meter.get("parity", "N"),
            meter.get("stop_bits", 1),
            meter.get("byte_size", 8),
            meter.get("timeout", 2.0),
            meter.get("one_based_map", True),
        )
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
            connection.commit()

    def list_meters(self) -> list[dict]:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT meter_id, meter_name, manufacturer, model, location, protocol, enabled,
                           seu, driver, com_port, slave_id, baud_rate, parity, stop_bits, byte_size, timeout, one_based_map
                    FROM meters
                    ORDER BY meter_name, meter_id;
                    """
                )
                return cursor.fetchall()

    def get_meter(self, meter_id: str) -> dict | None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT meter_id, meter_name, manufacturer, model, location, protocol, enabled,
                           seu, driver, com_port, slave_id, baud_rate, parity, stop_bits, byte_size, timeout, one_based_map
                    FROM meters
                    WHERE meter_id = %s;
                    """,
                    (meter_id,),
                )
                return cursor.fetchone()

    def find_enabled_connection_conflict(self, meter_id: str, protocol: str, com_port: str, slave_id: int) -> dict | None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT meter_id, meter_name, protocol, com_port, slave_id
                    FROM meters
                    WHERE enabled = TRUE
                      AND meter_id <> %s
                      AND protocol = %s
                      AND com_port = %s
                      AND slave_id = %s
                    LIMIT 1;
                    """,
                    (meter_id, protocol, com_port, slave_id),
                )
                return cursor.fetchone()

    def disable_meter(self, meter_id: str) -> None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE meters SET enabled = FALSE WHERE meter_id = %s;", (meter_id,))
            connection.commit()


class ReadingRepository:
    def __init__(
        self,
        connection: Connection | None = None,
        parameters: Iterable[dict] = (),
        settings: Settings | None = None,
    ) -> None:
        self.connection = connection
        self.parameters = list(parameters)
        self.settings = settings
        self._unique_conflict_target_available: bool | None = None

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
        return self.insert_readings(
            [
                {
                    "meter_id": meter_id,
                    "timestamp": timestamp,
                    "readings": readings,
                    "meter_timestamp": meter_timestamp,
                    "collected_at": collected_at,
                    "reading_date": reading_date,
                    "reading_time": reading_time,
                    "timestamp_source": timestamp_source,
                }
            ]
        )

    def _insert_columns(self) -> list[str]:
        parameter_by_column = {
            parameter_name_to_column_name(parameter["name"]): parameter
            for parameter in self.parameters
        }
        column_names = ordered_parameter_columns(parameter_by_column.values())
        return [
            "meter_id",
            "timestamp",
            "meter_timestamp",
            "collected_at",
            "reading_date",
            "reading_time",
            "timestamp_source",
        ] + column_names

    def _insert_values(self, payload: dict) -> list[object]:
        values = [
            payload["meter_id"],
            payload["timestamp"],
            payload.get("meter_timestamp"),
            payload.get("collected_at") or payload["timestamp"],
            payload.get("reading_date", ""),
            payload.get("reading_time", ""),
            payload.get("timestamp_source", "collector_fallback"),
        ]
        readings = payload.get("readings") or {}
        parameter_by_column = {
            parameter_name_to_column_name(parameter["name"]): parameter
            for parameter in self.parameters
        }
        for column_name in ordered_parameter_columns(parameter_by_column.values()):
            parameter = parameter_by_column[column_name]
            value = readings.get(parameter["name"])
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                value = round(value, 2)
            values.append(value)
        return values

    def insert_readings(self, reading_payloads: Sequence[dict]) -> bool:
        if not reading_payloads:
            return True

        if not self.unique_conflict_target_available():
            return self._insert_readings_with_legacy_duplicate_check(reading_payloads)

        sql_columns = self._insert_columns()
        row_placeholder = "(" + ", ".join(["%s"] * len(sql_columns)) + ")"
        placeholders = ", ".join([row_placeholder] * len(reading_payloads))
        insert_sql = (
            f"INSERT INTO readings ({', '.join(sql_columns)}) "
            f"VALUES {placeholders} "
            "ON CONFLICT (meter_id, timestamp, timestamp_source) DO NOTHING;"
        )
        values = [
            value
            for payload in reading_payloads
            for value in self._insert_values(payload)
        ]

        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(insert_sql, tuple(values))
                inserted_count = cursor.rowcount if cursor.rowcount >= 0 else 0
            connection.commit()
        return inserted_count == len(reading_payloads)

    def _insert_readings_with_legacy_duplicate_check(self, reading_payloads: Sequence[dict]) -> bool:
        sql_columns = self._insert_columns()
        placeholders = ", ".join(["%s"] * len(sql_columns))
        insert_sql = f"INSERT INTO readings ({', '.join(sql_columns)}) VALUES ({placeholders});"
        inserted_count = 0

        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                for payload in reading_payloads:
                    cursor.execute(
                        """
                        SELECT 1
                        FROM readings
                        WHERE meter_id = %s
                          AND timestamp = %s
                          AND timestamp_source = %s
                        LIMIT 1;
                        """,
                        (
                            payload["meter_id"],
                            payload["timestamp"],
                            payload.get("timestamp_source", "collector_fallback"),
                        ),
                    )
                    if cursor.fetchone() is not None:
                        continue
                    cursor.execute(insert_sql, tuple(self._insert_values(payload)))
                    inserted_count += 1
            connection.commit()
        return inserted_count == len(reading_payloads)

    def unique_conflict_target_available(self) -> bool:
        if self._unique_conflict_target_available is not None:
            return self._unique_conflict_target_available

        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_index i
                        JOIN pg_class t ON t.oid = i.indrelid
                        JOIN pg_namespace n ON n.oid = t.relnamespace
                        WHERE n.nspname = current_schema()
                          AND t.relname = 'readings'
                          AND i.indisunique
                          AND (
                              SELECT array_agg(a.attname ORDER BY key_position)
                              FROM unnest(i.indkey) WITH ORDINALITY AS keys(attnum, key_position)
                              JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = keys.attnum
                          ) = ARRAY['meter_id', 'timestamp', 'timestamp_source']::name[]
                    );
                    """
                )
                self._unique_conflict_target_available = bool(cursor.fetchone()[0])
        return self._unique_conflict_target_available

    def readings_table_is_partitioned(self) -> bool:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COALESCE((
                        SELECT c.relkind = 'p'
                        FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE n.nspname = current_schema()
                          AND c.relname = 'readings'
                    ), FALSE);
                    """
                )
                return bool(cursor.fetchone()[0])

    def drop_old_daily_reading_partitions(self, keep_days: int) -> int:
        bounded_keep_days = max(1, int(keep_days))
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM drop_old_daily_reading_partitions(%s, FALSE);", (bounded_keep_days,))
                dropped_count = len(cursor.fetchall())
            connection.commit()
        return dropped_count

    def ensure_daily_reading_partitions(self, days_back: int = 1, days_ahead: int = 7) -> int:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT ensure_daily_reading_partitions(%s, %s);",
                    (max(0, int(days_back)), max(0, int(days_ahead))),
                )
                ensured_count = int(cursor.fetchone()[0])
            connection.commit()
        return ensured_count

    def refresh_hourly_readings(self, hours_back: int = 2) -> int:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT refresh_hourly_readings(%s);", (max(1, int(hours_back)),))
                refreshed_count = int(cursor.fetchone()[0])
            connection.commit()
        return refreshed_count

    def delete_readings_older_than(self, cutoff: datetime, limit: int) -> int:
        bounded_limit = max(1, int(limit))
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    WITH expired AS (
                        SELECT id
                        FROM readings
                        WHERE collected_at < %s
                        ORDER BY collected_at ASC
                        LIMIT %s
                    )
                    DELETE FROM readings
                    USING expired
                    WHERE readings.id = expired.id
                    RETURNING readings.id;
                    """,
                    (cutoff, bounded_limit),
                )
                deleted_count = len(cursor.fetchall())
            connection.commit()
        return deleted_count


class AlertRuleRepository:
    def __init__(self, connection: Connection | None = None, settings: Settings | None = None) -> None:
        self.connection = connection
        self.settings = settings

    def list_rules(self, meter_id: str) -> list[dict]:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, meter_id, parameter_key, min_value, max_value, enabled, is_active,
                           last_value, last_triggered_at, last_cleared_at, created_at, updated_at
                    FROM alert_rules
                    WHERE meter_id = %s
                    ORDER BY parameter_key;
                    """,
                    (meter_id,),
                )
                return cursor.fetchall()

    def get_rule(self, rule_id: int) -> dict | None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, meter_id, parameter_key, min_value, max_value, enabled, is_active,
                           last_value, last_triggered_at, last_cleared_at, created_at, updated_at
                    FROM alert_rules
                    WHERE id = %s;
                    """,
                    (rule_id,),
                )
                return cursor.fetchone()

    def upsert_rule(self, rule: dict) -> dict:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO alert_rules (
                        meter_id, parameter_key, min_value, max_value, enabled, is_active,
                        last_value, last_triggered_at, last_cleared_at
                    )
                    VALUES (%s, %s, %s, %s, %s, FALSE, NULL, NULL, NULL)
                    ON CONFLICT (meter_id, parameter_key)
                    DO UPDATE SET
                        min_value = EXCLUDED.min_value,
                        max_value = EXCLUDED.max_value,
                        enabled = EXCLUDED.enabled,
                        updated_at = NOW()
                    RETURNING id, meter_id, parameter_key, min_value, max_value, enabled, is_active,
                              last_value, last_triggered_at, last_cleared_at, created_at, updated_at;
                    """,
                    (
                        rule["meter_id"],
                        rule["parameter_key"],
                        rule.get("min_value"),
                        rule.get("max_value"),
                        rule.get("enabled", True),
                    ),
                )
                saved = cursor.fetchone()
            connection.commit()
        return saved

    def delete_rule(self, rule_id: int) -> None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM alert_rules WHERE id = %s;", (rule_id,))
            connection.commit()

    def list_enabled_rules(self, meter_id: str) -> list[dict]:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, meter_id, parameter_key, min_value, max_value, enabled, is_active,
                           last_value, last_triggered_at, last_cleared_at
                    FROM alert_rules
                    WHERE meter_id = %s AND enabled = TRUE
                    ORDER BY parameter_key;
                    """,
                    (meter_id,),
                )
                return cursor.fetchall()

    def set_rule_state(
        self,
        *,
        rule_id: int,
        is_active: bool,
        last_value: float | None,
        triggered_at: datetime | None = None,
        cleared_at: datetime | None = None,
    ) -> None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE alert_rules
                    SET
                        is_active = %s,
                        last_value = %s,
                        last_triggered_at = COALESCE(%s, last_triggered_at),
                        last_cleared_at = COALESCE(%s, last_cleared_at),
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (is_active, last_value, triggered_at, cleared_at, rule_id),
                )
            connection.commit()

    def insert_event(self, event: dict) -> None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO alert_events (
                        rule_id, meter_id, parameter_key, parameter_label, measured_value,
                        min_value, max_value, event_type, event_time, reading_date, reading_time
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        event["rule_id"],
                        event["meter_id"],
                        event["parameter_key"],
                        event.get("parameter_label", ""),
                        event.get("measured_value"),
                        event.get("min_value"),
                        event.get("max_value"),
                        event["event_type"],
                        event["event_time"],
                        event.get("reading_date", ""),
                        event.get("reading_time", ""),
                    ),
                )
            connection.commit()

    def list_active_alerts(self, meter_id: str | None = None) -> list[dict]:
        where_clause = "WHERE ar.enabled = TRUE AND ar.is_active = TRUE"
        params: tuple[object, ...] = ()
        if meter_id:
            where_clause += " AND ar.meter_id = %s"
            params = (meter_id,)

        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT ar.id, ar.meter_id, ar.parameter_key, ar.min_value, ar.max_value, ar.last_value,
                           ar.last_triggered_at, ar.last_cleared_at, m.meter_name, m.location
                    FROM alert_rules ar
                    JOIN meters m ON m.meter_id = ar.meter_id
                    {where_clause}
                    ORDER BY ar.last_triggered_at DESC NULLS LAST, ar.parameter_key;
                    """,
                    params,
                )
                return cursor.fetchall()

    def list_alert_history(self, meter_id: str | None = None, limit: int = 50) -> list[dict]:
        where_clause = ""
        params: tuple[object, ...]
        if meter_id:
            where_clause = "WHERE ae.meter_id = %s"
            params = (meter_id, limit)
        else:
            params = (limit,)

        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT ae.id, ae.rule_id, ae.meter_id, ae.parameter_key, ae.parameter_label, ae.measured_value,
                           ae.min_value, ae.max_value, ae.event_type, ae.event_time, ae.reading_date, ae.reading_time,
                           m.meter_name, m.location
                    FROM alert_events ae
                    JOIN meters m ON m.meter_id = ae.meter_id
                    {where_clause}
                    ORDER BY ae.event_time DESC
                    LIMIT %s;
                    """,
                    params,
                )
                return cursor.fetchall()


class ReportScheduleRepository:
    def __init__(self, connection: Connection | None = None, settings: Settings | None = None) -> None:
        self.connection = connection
        self.settings = settings

    def _deserialize_schedule(self, record: dict) -> dict:
        schedule = dict(record)
        schedule["meter_ids"] = json.loads(schedule.get("meter_ids") or "[]")
        if not schedule["meter_ids"] and schedule.get("meter_id"):
            schedule["meter_ids"] = [schedule["meter_id"]]
        schedule["parameter_keys"] = json.loads(schedule.get("parameter_keys") or "[]")
        schedule["recipient_emails"] = json.loads(schedule.get("recipient_emails") or "[]")
        return schedule

    def list_schedules(self) -> list[dict]:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, meter_id, meter_ids, parameter_keys, recipient_emails, send_time, window_hours, enabled,
                           last_attempt_on, last_attempt_at, last_sent_on, last_sent_at, last_error, created_at, updated_at
                    FROM report_schedules
                    ORDER BY send_time, meter_id, id;
                    """
                )
                return [self._deserialize_schedule(record) for record in cursor.fetchall()]

    def upsert_schedule(self, schedule: dict) -> dict:
        schedule_id = schedule.get("id")
        meter_ids = json.dumps(schedule.get("meter_ids", []))
        parameter_keys = json.dumps(schedule.get("parameter_keys", []))
        recipient_emails = json.dumps(schedule.get("recipient_emails", []))

        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                if schedule_id:
                    cursor.execute(
                        """
                        UPDATE report_schedules
                        SET
                            meter_id = %s,
                            meter_ids = %s,
                            parameter_keys = %s,
                            recipient_emails = %s,
                            send_time = %s,
                            window_hours = %s,
                            enabled = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING id, meter_id, meter_ids, parameter_keys, recipient_emails, send_time, window_hours, enabled, last_attempt_on, last_attempt_at,
                                  last_sent_on, last_sent_at, last_error, created_at, updated_at;
                        """,
                        (
                            schedule["meter_id"],
                            meter_ids,
                            parameter_keys,
                            recipient_emails,
                            schedule["send_time"],
                            schedule.get("window_hours", 24),
                            schedule.get("enabled", True),
                            schedule_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO report_schedules (
                            meter_id, meter_ids, parameter_keys, recipient_emails, send_time, window_hours, enabled
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, meter_id, meter_ids, parameter_keys, recipient_emails, send_time, window_hours, enabled, last_attempt_on, last_attempt_at,
                                  last_sent_on, last_sent_at, last_error, created_at, updated_at;
                        """,
                        (
                            schedule["meter_id"],
                            meter_ids,
                            parameter_keys,
                            recipient_emails,
                            schedule["send_time"],
                            schedule.get("window_hours", 24),
                            schedule.get("enabled", True),
                        ),
                    )
                saved = cursor.fetchone()
            connection.commit()
        return self._deserialize_schedule(saved)

    def delete_schedule(self, schedule_id: int) -> None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM report_schedules WHERE id = %s;", (schedule_id,))
            connection.commit()

    def list_due_schedules(self, today: date, current_time_text: str) -> list[dict]:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, meter_id, meter_ids, parameter_keys, recipient_emails, send_time, window_hours, enabled,
                           last_attempt_on, last_attempt_at, last_sent_on, last_sent_at, last_error, created_at, updated_at
                    FROM report_schedules
                    WHERE enabled = TRUE
                      AND send_time <= %s
                      AND (last_attempt_on IS NULL OR last_attempt_on < %s)
                    ORDER BY send_time, id;
                    """,
                    (current_time_text, today),
                )
                return [self._deserialize_schedule(record) for record in cursor.fetchall()]

    def mark_sent(self, schedule_id: int, sent_on: date, sent_at: datetime) -> None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE report_schedules
                    SET
                        last_attempt_on = %s,
                        last_attempt_at = %s,
                        last_sent_on = %s,
                        last_sent_at = %s,
                        last_error = NULL,
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (sent_on, sent_at, sent_on, sent_at, schedule_id),
                )
            connection.commit()

    def mark_failed(self, schedule_id: int, error_message: str, attempted_on: date, attempted_at: datetime) -> None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE report_schedules
                    SET
                        last_attempt_on = %s,
                        last_attempt_at = %s,
                        last_error = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (attempted_on, attempted_at, error_message, schedule_id),
                )
            connection.commit()


class EmailSettingsRepository:
    def __init__(self, connection: Connection | None = None, settings: Settings | None = None) -> None:
        self.connection = connection
        self.settings = settings

    def get_settings(self) -> dict | None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from_email,
                           smtp_use_tls, smtp_use_ssl, updated_at
                    FROM email_settings
                    WHERE id = 1;
                    """
                )
                return cursor.fetchone()

    def upsert_settings(self, payload: dict) -> dict:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO email_settings (
                        id, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from_email, smtp_use_tls, smtp_use_ssl, updated_at
                    )
                    VALUES (1, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        smtp_host = EXCLUDED.smtp_host,
                        smtp_port = EXCLUDED.smtp_port,
                        smtp_username = EXCLUDED.smtp_username,
                        smtp_password = EXCLUDED.smtp_password,
                        smtp_from_email = EXCLUDED.smtp_from_email,
                        smtp_use_tls = EXCLUDED.smtp_use_tls,
                        smtp_use_ssl = EXCLUDED.smtp_use_ssl,
                        updated_at = NOW()
                    RETURNING id, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from_email,
                              smtp_use_tls, smtp_use_ssl, updated_at;
                    """,
                    (
                        payload.get("smtp_host", ""),
                        payload.get("smtp_port", 587),
                        payload.get("smtp_username", ""),
                        payload.get("smtp_password", ""),
                        payload.get("smtp_from_email", ""),
                        payload.get("smtp_use_tls", True),
                        payload.get("smtp_use_ssl", False),
                    ),
                )
                saved = cursor.fetchone()
            connection.commit()
        return saved


class RuntimeSettingsRepository:
    def __init__(self, connection: Connection | None = None, settings: Settings | None = None) -> None:
        self.connection = connection
        self.settings = settings

    def get_polling_settings(self) -> dict | None:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT poll_interval_seconds, updated_at
                    FROM runtime_settings
                    WHERE id = 1;
                    """
                )
                return cursor.fetchone()

    def upsert_poll_interval_seconds(self, poll_interval_seconds: int) -> dict:
        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO runtime_settings (id, poll_interval_seconds, updated_at)
                    VALUES (1, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET poll_interval_seconds = EXCLUDED.poll_interval_seconds, updated_at = NOW()
                    RETURNING poll_interval_seconds, updated_at;
                    """,
                    (poll_interval_seconds,),
                )
                saved = cursor.fetchone()
            connection.commit()
        return saved


"""
## FILE EXPLANATION
Purpose:
This file stores database read/write operations as simple repository classes.

Why this file exists:
SQL statements should stay inside the database layer so collector and service
layers do not mix business logic with SQL details.

What data enters the file:
Meter metadata and processed reading values from service layer.

What data leaves the file:
Database insert/update operations are executed. No complex object output.

Which layer of the architecture it belongs to:
Database Layer.

How it interacts with other files:
services/polling_service.py sends prepared values to these repositories.
main.py creates these repository objects after opening DB connection.
"""
