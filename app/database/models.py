import re
from typing import Iterable

from psycopg import Connection


def parameter_name_to_column_name(parameter_name: str) -> str:
    """Convert a human-readable parameter name into a safe PostgreSQL column name."""
    value = parameter_name.lower().strip()
    value = value.replace("+", " plus ")
    value = value.replace("-", " minus ")
    value = value.replace("&", "and")
    value = re.sub(r"[()]", "", value)
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def sql_type_for_parameter(parameter_type: str) -> str:
    """Map meter parameter types to PostgreSQL column types."""
    parameter_type = parameter_type.lower().strip()
    if parameter_type == "datetime4":
        return "TEXT"
    return "DOUBLE PRECISION"


def validate_parameter_columns(parameters: Iterable[dict]) -> None:
    seen: dict[str, str] = {}
    for parameter in parameters:
        parameter_name = parameter["name"]
        column_name = parameter_name_to_column_name(parameter_name)
        existing_name = seen.get(column_name)
        if existing_name is not None and existing_name != parameter_name:
            raise ValueError(
                f"Config parameters '{existing_name}' and '{parameter_name}' map to the same database column '{column_name}'."
            )
        seen[column_name] = parameter_name


def build_readings_table_sql(parameters: Iterable[dict]) -> str:
    lines = [
        "CREATE TABLE IF NOT EXISTS readings (",
        "    id BIGSERIAL PRIMARY KEY,",
        "    meter_id TEXT NOT NULL REFERENCES meters(meter_id),",
        "    timestamp TIMESTAMPTZ NOT NULL,",
        "    meter_timestamp TIMESTAMPTZ,",
        "    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),",
        "    reading_date TEXT NOT NULL DEFAULT '',",
        "    reading_time TEXT NOT NULL DEFAULT '',",
        "    timestamp_source TEXT NOT NULL DEFAULT 'collector_fallback',",
    ]

    for parameter in parameters:
        column_name = parameter_name_to_column_name(parameter["name"])
        column_type = sql_type_for_parameter(parameter["type"])
        lines.append(f"    {column_name} {column_type},")

    lines[-1] = lines[-1].rstrip(",")
    lines.append(");")
    return "\n".join(lines)


CREATE_METERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS meters (
    meter_id TEXT PRIMARY KEY,
    meter_name TEXT NOT NULL,
    manufacturer TEXT NOT NULL,
    model TEXT NOT NULL,
    location TEXT NOT NULL,
    protocol TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    seu BOOLEAN NOT NULL DEFAULT FALSE,
    driver TEXT NOT NULL DEFAULT 'schneider.pm5000',
    com_port TEXT NOT NULL DEFAULT '',
    slave_id INTEGER NOT NULL DEFAULT 1,
    baud_rate INTEGER NOT NULL DEFAULT 9600,
    parity TEXT NOT NULL DEFAULT 'N',
    stop_bits INTEGER NOT NULL DEFAULT 1,
    byte_size INTEGER NOT NULL DEFAULT 8,
    timeout DOUBLE PRECISION NOT NULL DEFAULT 2.0,
    one_based_map BOOLEAN NOT NULL DEFAULT TRUE
);
"""


CREATE_ALERT_RULES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS alert_rules (
    id BIGSERIAL PRIMARY KEY,
    meter_id TEXT NOT NULL REFERENCES meters(meter_id),
    parameter_key TEXT NOT NULL,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    last_value DOUBLE PRECISION,
    last_triggered_at TIMESTAMPTZ,
    last_cleared_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (meter_id, parameter_key)
);
"""


CREATE_ALERT_EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS alert_events (
    id BIGSERIAL PRIMARY KEY,
    rule_id BIGINT NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    meter_id TEXT NOT NULL REFERENCES meters(meter_id),
    parameter_key TEXT NOT NULL,
    parameter_label TEXT NOT NULL DEFAULT '',
    measured_value DOUBLE PRECISION,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    event_type TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    reading_date TEXT NOT NULL DEFAULT '',
    reading_time TEXT NOT NULL DEFAULT ''
);
"""


CREATE_REPORT_SCHEDULES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS report_schedules (
    id BIGSERIAL PRIMARY KEY,
    meter_id TEXT NOT NULL REFERENCES meters(meter_id),
    meter_ids TEXT NOT NULL DEFAULT '[]',
    parameter_keys TEXT NOT NULL DEFAULT '[]',
    recipient_emails TEXT NOT NULL DEFAULT '[]',
    send_time TEXT NOT NULL,
    window_hours INTEGER NOT NULL DEFAULT 24,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_attempt_on DATE,
    last_attempt_at TIMESTAMPTZ,
    last_sent_on DATE,
    last_sent_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


CREATE_EMAIL_SETTINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS email_settings (
    id SMALLINT PRIMARY KEY DEFAULT 1,
    smtp_host TEXT NOT NULL DEFAULT '',
    smtp_port INTEGER NOT NULL DEFAULT 587,
    smtp_username TEXT NOT NULL DEFAULT '',
    smtp_password TEXT NOT NULL DEFAULT '',
    smtp_from_email TEXT NOT NULL DEFAULT '',
    smtp_use_tls BOOLEAN NOT NULL DEFAULT TRUE,
    smtp_use_ssl BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def create_tables(connection: Connection, parameters: Iterable[dict]) -> None:
    parameter_list = list(parameters)
    validate_parameter_columns(parameter_list)
    expected_columns = {
        parameter_name_to_column_name(parameter["name"]): sql_type_for_parameter(parameter["type"])
        for parameter in parameter_list
    }

    with connection.cursor() as cursor:
        cursor.execute(CREATE_METERS_TABLE_SQL)
        cursor.execute(CREATE_ALERT_RULES_TABLE_SQL)
        cursor.execute(CREATE_ALERT_EVENTS_TABLE_SQL)
        cursor.execute(CREATE_REPORT_SCHEDULES_TABLE_SQL)
        cursor.execute(CREATE_EMAIL_SETTINGS_TABLE_SQL)

        # Create the base table once, then keep adding any new config-driven columns.
        cursor.execute(build_readings_table_sql(parameter_list))
        for column_name, column_type in expected_columns.items():
            cursor.execute(f"ALTER TABLE readings ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        cursor.execute("ALTER TABLE readings ADD COLUMN IF NOT EXISTS meter_timestamp TIMESTAMPTZ;")
        cursor.execute("ALTER TABLE readings ADD COLUMN IF NOT EXISTS collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW();")
        cursor.execute("ALTER TABLE readings ADD COLUMN IF NOT EXISTS reading_date TEXT NOT NULL DEFAULT '';")
        cursor.execute("ALTER TABLE readings ADD COLUMN IF NOT EXISTS reading_time TEXT NOT NULL DEFAULT '';")
        cursor.execute("ALTER TABLE readings ADD COLUMN IF NOT EXISTS timestamp_source TEXT NOT NULL DEFAULT 'collector_fallback';")
        cursor.execute(
            """
            UPDATE readings
            SET
                collected_at = COALESCE(collected_at, timestamp),
                meter_timestamp = COALESCE(meter_timestamp, timestamp),
                reading_date = CASE
                    WHEN reading_date = '' THEN TO_CHAR(COALESCE(meter_timestamp, timestamp), 'DD/MM/YYYY')
                    ELSE reading_date
                END,
                reading_time = CASE
                    WHEN reading_time = '' THEN TO_CHAR(COALESCE(meter_timestamp, timestamp), 'HH24:MI:SS')
                    ELSE reading_time
                END,
                timestamp_source = CASE
                    WHEN timestamp_source = '' THEN 'collector_fallback'
                    ELSE timestamp_source
                END
            WHERE
                collected_at IS NULL
                OR meter_timestamp IS NULL
                OR reading_date = ''
                OR reading_time = ''
                OR timestamp_source = '';
            """
        )

        meter_columns = {
            "seu": "BOOLEAN NOT NULL DEFAULT FALSE",
            "driver": "TEXT NOT NULL DEFAULT 'schneider.pm5000'",
            "com_port": "TEXT NOT NULL DEFAULT ''",
            "slave_id": "INTEGER NOT NULL DEFAULT 1",
            "baud_rate": "INTEGER NOT NULL DEFAULT 9600",
            "parity": "TEXT NOT NULL DEFAULT 'N'",
            "stop_bits": "INTEGER NOT NULL DEFAULT 1",
            "byte_size": "INTEGER NOT NULL DEFAULT 8",
            "timeout": "DOUBLE PRECISION NOT NULL DEFAULT 2.0",
            "one_based_map": "BOOLEAN NOT NULL DEFAULT TRUE",
        }
        for column_name, column_definition in meter_columns.items():
            cursor.execute(f"ALTER TABLE meters ADD COLUMN IF NOT EXISTS {column_name} {column_definition};")
        cursor.execute("ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS last_attempt_on DATE;")
        cursor.execute("ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ;")
        cursor.execute("ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS window_hours INTEGER NOT NULL DEFAULT 24;")
        cursor.execute("ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS meter_ids TEXT NOT NULL DEFAULT '[]';")
        cursor.execute(
            """
            UPDATE report_schedules
            SET meter_ids = CONCAT('["', meter_id, '"]')
            WHERE meter_ids = '[]' OR meter_ids = '';
            """
        )
        cursor.execute("ALTER TABLE email_settings ADD COLUMN IF NOT EXISTS smtp_host TEXT NOT NULL DEFAULT '';")
        cursor.execute("ALTER TABLE email_settings ADD COLUMN IF NOT EXISTS smtp_port INTEGER NOT NULL DEFAULT 587;")
        cursor.execute("ALTER TABLE email_settings ADD COLUMN IF NOT EXISTS smtp_username TEXT NOT NULL DEFAULT '';")
        cursor.execute("ALTER TABLE email_settings ADD COLUMN IF NOT EXISTS smtp_password TEXT NOT NULL DEFAULT '';")
        cursor.execute("ALTER TABLE email_settings ADD COLUMN IF NOT EXISTS smtp_from_email TEXT NOT NULL DEFAULT '';")
        cursor.execute("ALTER TABLE email_settings ADD COLUMN IF NOT EXISTS smtp_use_tls BOOLEAN NOT NULL DEFAULT TRUE;")
        cursor.execute("ALTER TABLE email_settings ADD COLUMN IF NOT EXISTS smtp_use_ssl BOOLEAN NOT NULL DEFAULT FALSE;")
        cursor.execute("ALTER TABLE email_settings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();")
        cursor.execute(
            """
            INSERT INTO email_settings (
                id, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from_email, smtp_use_tls, smtp_use_ssl
            )
            VALUES (1, '', 587, '', '', '', TRUE, FALSE)
            ON CONFLICT (id) DO NOTHING;
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_readings_meter_timestamp_desc
            ON readings (meter_id, timestamp DESC);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_readings_meter_collected_desc
            ON readings (meter_id, collected_at DESC);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_readings_collected_at
            ON readings (collected_at);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_readings_meter_timestamp_source
            ON readings (meter_id, timestamp, timestamp_source);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_meters_meter_id
            ON meters (meter_id);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alert_rules_meter_parameter
            ON alert_rules (meter_id, parameter_key);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alert_events_meter_time
            ON alert_events (meter_id, event_time DESC);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_report_schedules_enabled_time
            ON report_schedules (enabled, send_time, window_hours);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_email_settings_id
            ON email_settings (id);
            """
        )
    connection.commit()


"""
## FILE EXPLANATION
Purpose:
This file defines and creates database tables for meters and readings.

Why this file exists:
Schema creation should be centralized and independent from meter collection code.

What data enters the file:
A live PostgreSQL connection object.

What data leaves the file:
No return data. It creates/updates table structure in the database.

Which layer of the architecture it belongs to:
Database Layer.

How it interacts with other files:
Called by main.py during startup before polling begins.
Repositories then use these tables for insert/read operations.
"""
