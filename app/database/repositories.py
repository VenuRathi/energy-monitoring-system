if __package__ is None or __package__ == "":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from contextlib import contextmanager
from datetime import date, datetime
import json
from typing import Iterable

from psycopg import Connection
from psycopg.rows import dict_row

from app.database.connection import get_connection
from app.database.models import parameter_name_to_column_name
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
        column_names = [parameter_name_to_column_name(parameter["name"]) for parameter in self.parameters]
        sql_columns = [
            "meter_id",
            "timestamp",
            "meter_timestamp",
            "collected_at",
            "reading_date",
            "reading_time",
            "timestamp_source",
        ] + column_names
        placeholders = ", ".join(["%s"] * len(sql_columns))
        sql = f"INSERT INTO readings ({', '.join(sql_columns)}) VALUES ({placeholders});"

        values = [
            meter_id,
            timestamp,
            meter_timestamp,
            collected_at or timestamp,
            reading_date,
            reading_time,
            timestamp_source,
        ]
        for parameter in self.parameters:
            values.append(readings.get(parameter["name"]))

        with _repository_connection(self.connection, self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 1
                    FROM readings
                    WHERE meter_id = %s
                      AND timestamp = %s
                      AND timestamp_source = %s
                    LIMIT 1;
                    """,
                    (meter_id, timestamp, timestamp_source),
                )
                if cursor.fetchone() is not None:
                    return False
                cursor.execute(sql, tuple(values))
            connection.commit()
        return True

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
