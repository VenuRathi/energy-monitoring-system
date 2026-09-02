import os
import smtplib
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.api import server as api_server
from app.api import service as api_service
from app.collectors.modbus_client import ModbusRTUClient
from app.database.connection import get_connection
from app.database.models import build_readings_table_sql, create_tables, validate_parameter_columns
from app.database.repositories import MeterRepository, ReadingRepository
from app.runtime_state import (
    get_schema_startup_state,
    record_meter_runtime_error,
    record_schema_startup_failure,
    record_schema_startup_success,
)
from app.services.polling_service import PollingService
from app.services.retention_service import ReadingsRetentionService
from config.settings import load_settings


class SettingsAndModelsTests(unittest.TestCase):
    def test_settings_parse_allowed_origins(self) -> None:
        with patch.dict(
            os.environ,
            {
                "API_ALLOWED_ORIGINS": "http://127.0.0.1:5173, http://localhost:5173",
                "API_DEBUG": "false",
            },
            clear=False,
        ):
            settings = load_settings()

        self.assertEqual(
            settings.api_allowed_origins,
            ("http://127.0.0.1:5173", "http://localhost:5173"),
        )
        self.assertFalse(settings.api_debug)

    def test_polling_interval_defaults_to_production_value(self) -> None:
        with patch.dict(os.environ, {"POLL_INTERVAL_SECONDS": ""}, clear=False):
            os.environ.pop("POLL_INTERVAL_SECONDS", None)
            settings = load_settings()

        self.assertEqual(settings.poll_interval_seconds, 180)

    def test_meter_freshness_uses_live_saved_polling_interval(self) -> None:
        recent_update = datetime.now(timezone.utc) - timedelta(seconds=500)
        meter = {"enabled": True, "last_update": recent_update}

        with patch.object(api_service, "get_runtime_poll_interval_seconds", return_value=900):
            self.assertEqual(api_service._effective_meter_communication_status(meter), "online")
            self.assertFalse(api_service._meter_stale_warning(meter))

    def test_polling_settings_api_validation_and_save(self) -> None:
        class FakeRuntimeSettingsRepository:
            def __init__(self, settings) -> None:
                self.settings = settings

            def upsert_poll_interval_seconds(self, value):
                return {"poll_interval_seconds": value, "updated_at": None}

        runtime_settings = SimpleNamespace(enable_database=True, poll_interval_seconds=180)
        with patch("app.api.service.get_runtime_settings", return_value=runtime_settings), patch(
            "app.api.service.RuntimeSettingsRepository", FakeRuntimeSettingsRepository
        ):
            saved = api_service.save_polling_settings({"pollIntervalSeconds": 18})
            self.assertEqual(saved["pollIntervalSeconds"], 18)
            with self.assertRaises(ValueError):
                api_service.save_polling_settings({"pollIntervalSeconds": 9})
            with self.assertRaises(ValueError):
                api_service.save_polling_settings({"pollIntervalSeconds": "18.5"})

    def test_validate_parameter_columns_rejects_collisions(self) -> None:
        parameters = [
            {"name": "Power Factor (Total)", "type": "float32"},
            {"name": "Power Factor Total", "type": "float32"},
        ]

        with self.assertRaises(ValueError):
            validate_parameter_columns(parameters)

    def test_readings_table_ddl_is_partitioned_and_database_deduplicated(self) -> None:
        ddl = build_readings_table_sql(
            [
                {"name": "Frequency", "type": "float32"},
                {"name": "Frequency", "type": "float32"},
                {"name": "Active Energy Delivered / Import", "type": "int64"},
                {"name": "Reactive Energy Delivered / Import", "type": "int64"},
                {"name": "Apparent Energy Delivered / Import", "type": "int64"},
            ]
        )

        self.assertIn("PARTITION BY RANGE (timestamp)", ddl)
        self.assertIn("PRIMARY KEY (timestamp, id)", ddl)
        self.assertIn("UNIQUE (meter_id, timestamp, timestamp_source)", ddl)
        self.assertIn("frequency NUMERIC(20,2)", ddl)
        self.assertEqual(ddl.count("frequency NUMERIC(20,2)"), 1)
        self.assertIn("active_energy_received_out_of_load NUMERIC(20,3)", ddl)
        self.assertIn("meter_id TEXT NOT NULL REFERENCES meters(meter_id),\n    meter_name TEXT", ddl)
        self.assertLess(ddl.index("timestamp_source"), ddl.index("active_energy_received_out_of_load"))
        self.assertLess(
            ddl.index("active_energy_received_out_of_load"),
            ddl.index("reactive_energy_received"),
        )
        self.assertLess(
            ddl.index("reactive_energy_received"),
            ddl.index("apparent_energy_received"),
        )

    def test_create_tables_applies_hourly_and_schema_views_sql(self) -> None:
        class FakeCursor:
            def __init__(self) -> None:
                self.executed_sql = []
                self.fetchone_values = [(True,), (1,)]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def execute(self, query, params=None) -> None:
                self.executed_sql.append(str(query))

            def fetchone(self):
                return self.fetchone_values.pop(0)

        class FakeConnection:
            def __init__(self) -> None:
                self.cursor_instance = FakeCursor()
                self.committed = False

            def cursor(self):
                return self.cursor_instance

            def commit(self) -> None:
                self.committed = True

        original_read_text = Path.read_text

        def fake_exists(self):
            return self.name in {"hourly_readings.sql", "schema_views.sql"}

        def fake_read_text(self, encoding="utf-8"):
            if self.name == "hourly_readings.sql":
                return "CREATE TABLE IF NOT EXISTS hourly_readings (id integer);"
            if self.name == "schema_views.sql":
                return "CREATE OR REPLACE VIEW meter_latest_readings AS SELECT 1;"
            return original_read_text(self, encoding=encoding)

        connection = FakeConnection()
        with patch.object(Path, "exists", fake_exists), patch.object(Path, "read_text", fake_read_text):
            create_tables(connection, [{"name": "Frequency", "type": "float32"}], poll_interval_seconds=180)

        self.assertTrue(connection.committed)
        self.assertTrue(any("hourly_readings" in statement for statement in connection.cursor_instance.executed_sql))
        self.assertTrue(any("meter_latest_readings" in statement for statement in connection.cursor_instance.executed_sql))

    def test_datetime4_decode_matches_sheet_layout(self) -> None:
        service = PollingService(
            meter_config={"meter_id": "MTR-001", "parameters": []},
            collector=None,
            poll_interval_seconds=10,
        )

        decoded = service._decode_datetime4_raw("001A-061A-0E30-4C32")

        self.assertIsNotNone(decoded)
        assert decoded is not None
        self.assertEqual(decoded.year, 2026)
        self.assertEqual(decoded.month, 6)
        self.assertEqual(decoded.day, 26)
        self.assertEqual(decoded.hour, 14)
        self.assertEqual(decoded.minute, 48)
        self.assertEqual(decoded.second, 19)
        self.assertEqual(decoded.microsecond, 506000)

    def test_database_connection_uses_bounded_timeout_and_application_name(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DB_CONNECT_TIMEOUT_SECONDS": "9",
                "API_DEBUG": "false",
            },
            clear=False,
        ):
            settings = load_settings()

        with patch("app.database.connection.psycopg.connect") as connect:
            get_connection(settings)

        connect.assert_called_once()
        self.assertEqual(connect.call_args.kwargs["connect_timeout"], 9)
        self.assertEqual(connect.call_args.kwargs["application_name"], "energy_monitoring_system")

    def test_modbus_client_reset_clears_reconnect_cooldown(self) -> None:
        class FakeClient:
            def close(self) -> None:
                return None

        client = ModbusRTUClient(
            port="COM5",
            baud_rate=9600,
            parity="N",
            stop_bits=1,
            byte_size=8,
            slave_id=1,
        )
        client._client = FakeClient()
        client._last_connect_attempt_monotonic = 123.45

        client._reset_client()

        self.assertIsNone(client._client)
        self.assertEqual(client._last_connect_attempt_monotonic, 0.0)

    def test_settings_parse_readings_retention_controls(self) -> None:
        with patch.dict(
            os.environ,
            {
                "READINGS_RETENTION_DAYS": "365",
                "READINGS_CLEANUP_BATCH_SIZE": "123",
                "READINGS_CLEANUP_INTERVAL_HOURS": "6",
                "READINGS_INSERT_BUFFER_ROWS": "77",
                "READINGS_INSERT_BUFFER_SECONDS": "8",
                "HOURLY_AGGREGATE_REFRESH_INTERVAL_MINUTES": "11",
                "API_DEBUG": "false",
            },
            clear=False,
        ):
            settings = load_settings()

        self.assertEqual(settings.readings_retention_days, 365)
        self.assertEqual(settings.readings_cleanup_batch_size, 123)
        self.assertEqual(settings.readings_cleanup_interval_hours, 6)
        self.assertEqual(settings.readings_insert_buffer_rows, 77)
        self.assertEqual(settings.readings_insert_buffer_seconds, 8)
        self.assertEqual(settings.hourly_aggregate_refresh_interval_minutes, 11)

    def test_retention_service_uses_partition_drop_when_available(self) -> None:
        class FakeReadingRepository:
            def __init__(self) -> None:
                self.ensured = False
                self.keep_days = None

            def readings_table_is_partitioned(self):
                return True

            def ensure_daily_reading_partitions(self, days_back, days_ahead):
                self.ensured = True
                return 9

            def drop_old_daily_reading_partitions(self, keep_days):
                self.keep_days = keep_days
                return 3

        repository = FakeReadingRepository()
        with patch.dict(
            os.environ,
            {
                "READINGS_RETENTION_DAYS": "30",
                "READINGS_CLEANUP_BATCH_SIZE": "250",
                "API_DEBUG": "false",
            },
            clear=False,
        ):
            settings = load_settings()

        removed = ReadingsRetentionService(settings, repository).cleanup_once(
            datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
        )

        self.assertEqual(removed, 3)
        self.assertTrue(repository.ensured)
        self.assertEqual(repository.keep_days, 30)

    def test_retention_service_falls_back_to_bounded_delete_before_partition_migration(self) -> None:
        class FakeReadingRepository:
            def __init__(self) -> None:
                self.cutoff = None
                self.limit = None

            def readings_table_is_partitioned(self):
                return False

            def delete_readings_older_than(self, cutoff, limit):
                self.cutoff = cutoff
                self.limit = limit
                return 7

        repository = FakeReadingRepository()
        with patch.dict(
            os.environ,
            {
                "READINGS_RETENTION_DAYS": "30",
                "READINGS_CLEANUP_BATCH_SIZE": "250",
                "API_DEBUG": "false",
            },
            clear=False,
        ):
            settings = load_settings()

        deleted = ReadingsRetentionService(settings, repository).cleanup_once(
            datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
        )

        self.assertEqual(deleted, 7)
        self.assertEqual(repository.limit, 250)
        self.assertEqual(repository.cutoff, datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc))

    def test_duplicate_reading_is_skipped_by_on_conflict(self) -> None:
        class FakeCursor:
            def __init__(self) -> None:
                self.executed_sql = []
                self.rowcount = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def execute(self, query, params=None) -> None:
                self.executed_sql.append(str(query))

        class FakeConnection:
            def __init__(self) -> None:
                self.cursor_instance = FakeCursor()
                self.committed = False

            def cursor(self):
                return self.cursor_instance

            def commit(self) -> None:
                self.committed = True

        connection = FakeConnection()
        repository = ReadingRepository(connection=connection, parameters=[])
        repository.unique_conflict_target_available = lambda: True
        inserted = repository.insert_reading(
            meter_id="MTR-001",
            timestamp=datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc),
            readings={},
            timestamp_source="meter",
        )

        self.assertFalse(inserted)
        self.assertTrue(connection.committed)
        self.assertEqual(len(connection.cursor_instance.executed_sql), 1)
        self.assertIn("INSERT INTO readings", connection.cursor_instance.executed_sql[0])
        self.assertIn("ON CONFLICT (meter_id, timestamp, timestamp_source) DO NOTHING", connection.cursor_instance.executed_sql[0])

    def test_unique_conflict_target_check_compares_matching_postgres_array_types(self) -> None:
        class FakeCursor:
            def __init__(self) -> None:
                self.executed_sql = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def execute(self, query, params=None) -> None:
                self.executed_sql.append(str(query))

            def fetchone(self):
                return (True,)

        class FakeConnection:
            def __init__(self) -> None:
                self.cursor_instance = FakeCursor()

            def cursor(self):
                return self.cursor_instance

        connection = FakeConnection()
        repository = ReadingRepository(connection=connection, parameters=[])

        self.assertTrue(repository.unique_conflict_target_available())
        self.assertIn(
            "ARRAY['meter_id', 'timestamp', 'timestamp_source']::name[]",
            connection.cursor_instance.executed_sql[0],
        )

    def test_new_reading_is_inserted_and_committed(self) -> None:
        class FakeCursor:
            def __init__(self) -> None:
                self.executed_sql = []
                self.rowcount = 1

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def execute(self, query, params=None) -> None:
                self.executed_sql.append(str(query))

        class FakeConnection:
            def __init__(self) -> None:
                self.cursor_instance = FakeCursor()
                self.committed = False

            def cursor(self):
                return self.cursor_instance

            def commit(self) -> None:
                self.committed = True

        connection = FakeConnection()
        repository = ReadingRepository(connection=connection, parameters=[])
        repository.unique_conflict_target_available = lambda: True
        inserted = repository.insert_reading(
            meter_id="MTR-001",
            timestamp=datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc),
            readings={},
            timestamp_source="meter",
        )

        self.assertTrue(inserted)
        self.assertTrue(connection.committed)
        self.assertEqual(len(connection.cursor_instance.executed_sql), 1)
        self.assertIn("INSERT INTO readings", connection.cursor_instance.executed_sql[0])

    def test_legacy_duplicate_check_is_used_when_unique_constraint_is_missing(self) -> None:
        class FakeCursor:
            def __init__(self) -> None:
                self.executed_sql = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def execute(self, query, params=None) -> None:
                self.executed_sql.append(str(query))

            def fetchone(self):
                return (1,)

        class FakeConnection:
            def __init__(self) -> None:
                self.cursor_instance = FakeCursor()
                self.committed = False

            def cursor(self):
                return self.cursor_instance

            def commit(self) -> None:
                self.committed = True

        connection = FakeConnection()
        repository = ReadingRepository(connection=connection, parameters=[])
        repository.unique_conflict_target_available = lambda: False

        inserted = repository.insert_reading(
            meter_id="MTR-001",
            timestamp=datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc),
            readings={},
            timestamp_source="meter",
        )

        self.assertFalse(inserted)
        self.assertTrue(connection.committed)
        self.assertEqual(len(connection.cursor_instance.executed_sql), 1)
        self.assertIn("SELECT 1", connection.cursor_instance.executed_sql[0])

    def test_report_exports_require_api_key_when_enabled(self) -> None:
        original_enabled = api_server.SETTINGS.api_key_enabled
        original_key = api_server.SETTINGS.api_key
        api_server.SETTINGS.api_key_enabled = True
        api_server.SETTINGS.api_key = "secret-key"
        self.addCleanup(lambda: setattr(api_server.SETTINGS, "api_key_enabled", original_enabled))
        self.addCleanup(lambda: setattr(api_server.SETTINGS, "api_key", original_key))

        with patch("app.api.server.ensure_schema"), patch.object(api_server.SETTINGS, "api_key_enabled", False):
            app = api_server.create_app()
        app.testing = True

        response = app.test_client().post("/api/reports/excel", json={})

        self.assertEqual(response.status_code, 401)
        self.assertIn("Missing API key", response.get_json()["error"])

    def test_smtp_environment_password_overrides_saved_database_password(self) -> None:
        class FakeEmailSettingsRepository:
            def __init__(self, settings) -> None:
                self.settings = settings

            def get_settings(self):
                return {
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "smtp_username": "alerts@example.com",
                    "smtp_password": "db-secret",
                    "smtp_from_email": "alerts@example.com",
                    "smtp_use_tls": True,
                    "smtp_use_ssl": False,
                    "updated_at": None,
                }

        with patch.dict(
            os.environ,
            {
                "ENABLE_DATABASE": "true",
                "SMTP_PASSWORD": "env-secret",
                "API_DEBUG": "false",
            },
            clear=False,
        ):
            settings = load_settings()

        with patch("app.api.service.get_runtime_settings", return_value=settings), patch(
            "app.api.service.EmailSettingsRepository",
            FakeEmailSettingsRepository,
        ):
            effective = api_service._effective_email_settings()
            serialized = api_service.get_email_settings()

        self.assertEqual(effective["smtp_password"], "env-secret")
        self.assertEqual(effective["source"], "database+env-secret")
        self.assertTrue(serialized["hasPassword"])
        self.assertEqual(serialized["source"], "database+env-secret")

    def test_placeholder_smtp_environment_password_does_not_override_database_password(self) -> None:
        class FakeEmailSettingsRepository:
            def __init__(self, settings) -> None:
                self.settings = settings

            def get_settings(self):
                return {
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": 587,
                    "smtp_username": "alerts@example.com",
                    "smtp_password": "db-app-password",
                    "smtp_from_email": "alerts@example.com",
                    "smtp_use_tls": True,
                    "smtp_use_ssl": False,
                    "updated_at": None,
                }

        with patch.dict(
            os.environ,
            {
                "ENABLE_DATABASE": "true",
                "SMTP_PASSWORD": "replace_me",
                "API_DEBUG": "false",
            },
            clear=False,
        ):
            settings = load_settings()

        with patch("app.api.service.get_runtime_settings", return_value=settings), patch(
            "app.api.service.EmailSettingsRepository",
            FakeEmailSettingsRepository,
        ):
            effective = api_service._effective_email_settings()
            serialized = api_service.get_email_settings()

        self.assertEqual(settings.smtp_password, "")
        self.assertEqual(effective["smtp_password"], "db-app-password")
        self.assertEqual(effective["source"], "database")
        self.assertTrue(serialized["hasPassword"])
        self.assertEqual(serialized["source"], "database")

    def test_smtp_authentication_error_returns_actionable_message(self) -> None:
        class FakeSmtpClient:
            def __init__(self, host, port, timeout=None) -> None:
                self.host = host
                self.port = port
                self.timeout = timeout

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def starttls(self) -> None:
                return None

            def login(self, username, password) -> None:
                raise smtplib.SMTPAuthenticationError(535, b"BadCredentials")

            def send_message(self, message) -> None:
                raise AssertionError("send_message should not be called after failed login.")

        email_settings = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": "venurathi4@gmail.com",
            "smtp_password": "bad-password",
            "smtp_from_email": "venurathi4@gmail.com",
            "smtp_use_tls": True,
            "smtp_use_ssl": False,
        }

        with patch("app.api.service.smtplib.SMTP", FakeSmtpClient):
            with self.assertRaises(ValueError) as context:
                api_service._send_email_with_attachment(
                    recipient_emails=["operator@example.com"],
                    subject="Test",
                    body="Body",
                    attachment_bytes=b"report",
                    filename="report.txt",
                    mime_type="text/plain",
                    email_settings=email_settings,
                )

        self.assertIn("SMTP authentication failed", str(context.exception))
        self.assertIn("Google app password", str(context.exception))

    def test_report_email_uses_screen_printing_subject_and_excel_attachment(self) -> None:
        captured_email = {}

        def fake_send_email(**kwargs) -> None:
            captured_email.update(kwargs)

        payload = {
            "meterIds": ["MTR-001"],
            "parameterKeys": ["active_power_total"],
            "recipientEmails": ["operator@example.com"],
            "startDateTime": "2026-08-01T00:00:00+05:30",
            "endDateTime": "2026-08-01T01:00:00+05:30",
        }
        export_payload = {
            "bytes": b"xlsx-bytes",
            "filename": "screen_printing.xlsx",
            "meter_name": "Screen Printing",
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "rows": 1,
        }

        with patch("app.api.service.build_export_payload", return_value=export_payload), patch(
            "app.api.service._send_email_with_attachment",
            side_effect=fake_send_email,
        ):
            result = api_service.send_report_email(payload)

        self.assertTrue(result["sent"])
        self.assertEqual(captured_email["subject"], "OSP Screen Printing ems")
        self.assertTrue(captured_email["body"].startswith("Please find the Excel sheet attached below."))
        self.assertEqual(captured_email["attachment_bytes"], b"xlsx-bytes")
        self.assertEqual(captured_email["filename"], "screen_printing.xlsx")
        self.assertEqual(
            captured_email["mime_type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_email_route_maps_smtp_auth_failure_without_internal_server_error(self) -> None:
        with patch("app.api.server.ensure_schema"):
            app = api_server.create_app()
        app.testing = True

        with patch.object(api_server.SETTINGS, "api_key_enabled", False), patch(
            "app.api.server.send_report_email",
            side_effect=smtplib.SMTPAuthenticationError(535, b"BadCredentials"),
        ):
            response = app.test_client().post(
                "/api/reports/email",
                json={
                    "meterIds": ["MTR-001"],
                    "parameterKeys": ["active_power_total"],
                    "recipientEmails": ["operator@example.com"],
                    "startDateTime": "2026-08-02T00:00:00+05:30",
                    "endDateTime": "2026-08-02T01:00:00+05:30",
                },
            )

        body = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body["status"], "fail")
        self.assertIn("SMTP authentication failed", body["error"])
        self.assertNotIn("Internal server error", body["error"])

    def test_disable_meter_only_marks_meter_disabled_and_preserves_history_tables(self) -> None:
        class FakeCursor:
            def __init__(self) -> None:
                self.executed = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def execute(self, query, params=None) -> None:
                self.executed.append((str(query), params))

        class FakeConnection:
            def __init__(self) -> None:
                self.cursor_instance = FakeCursor()
                self.committed = False

            def cursor(self):
                return self.cursor_instance

            def commit(self) -> None:
                self.committed = True

        connection = FakeConnection()
        MeterRepository(connection=connection).disable_meter("MTR-001")

        self.assertTrue(connection.committed)
        self.assertEqual(len(connection.cursor_instance.executed), 1)
        executed_sql, params = connection.cursor_instance.executed[0]
        self.assertIn("UPDATE meters SET enabled = FALSE", executed_sql)
        self.assertNotIn("readings", executed_sql.lower())
        self.assertEqual(params, ("MTR-001",))

    def test_enable_meter_preserves_connection_and_serial_settings(self) -> None:
        saved_payloads = []

        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

        class FakeMeterRepository:
            def __init__(self, connection) -> None:
                self.connection = connection

            def find_enabled_connection_conflict(self, **kwargs):
                return None

            def upsert_meter(self, meter):
                saved_payloads.append(dict(meter))

        payload = {
            "meter_id": "mtr-901",
            "meter_name": "Recovered Meter",
            "location": "Panel A",
            "manufacturer": "Schneider",
            "model": "PM5000-EM6400",
            "protocol": "modbus_rtu",
            "enabled": True,
            "seu": False,
            "driver": "schneider.pm5000",
            "com_port": " com06 ",
            "slave_id": 17,
            "baud_rate": 19200,
            "parity": "e",
            "stop_bits": 2,
            "byte_size": 7,
            "timeout": 3.5,
            "one_based_map": False,
        }

        with patch("app.api.service._open_connection", return_value=FakeConnection()), patch(
            "app.api.service.MeterRepository",
            FakeMeterRepository,
        ):
            saved = api_service.save_meter(payload)

        self.assertEqual(saved["meter_id"], "MTR-901")
        self.assertTrue(saved["enabled"])
        self.assertEqual(saved["com_port"], "COM6")
        self.assertEqual(saved["slave_id"], 17)
        self.assertEqual(saved["baud_rate"], 19200)
        self.assertEqual(saved["parity"], "E")
        self.assertEqual(saved["stop_bits"], 2)
        self.assertEqual(saved["byte_size"], 7)
        self.assertEqual(saved["timeout"], 3.5)
        self.assertFalse(saved["one_based_map"])
        self.assertEqual(saved_payloads, [saved])

    def test_disabled_meter_status_ignores_stale_runtime_diagnostic(self) -> None:
        record_meter_runtime_error(
            "MTR-PH5-DISABLED",
            error_at=datetime(2026, 7, 31, 11, 0, tzinfo=timezone.utc),
            error_message="Old COM failure",
            diagnostic_code="com_port_missing",
            diagnostic_message="COM port missing: old adapter issue.",
            communication_status="warning",
        )

        meter = api_service._row_to_meter(
            {
                "meter_id": "MTR-PH5-DISABLED",
                "meter_name": "Disabled Meter",
                "location": "Panel A",
                "manufacturer": "Schneider",
                "model": "PM5000-EM6400",
                "protocol": "modbus_rtu",
                "enabled": False,
                "seu": False,
                "driver": "schneider.pm5000",
                "com_port": "COM6",
                "slave_id": 1,
                "baud_rate": 9600,
                "parity": "N",
                "stop_bits": 1,
                "byte_size": 8,
                "timeout": 2.0,
                "one_based_map": True,
            }
        )

        self.assertEqual(meter["status"], "offline")
        self.assertEqual(meter["data_quality"], "disabled")
        self.assertEqual(meter["status_detail"], "Meter is disabled and not being polled.")
        self.assertEqual(meter["diagnosticCode"], "")
        self.assertEqual(meter["diagnosticMessage"], "")

    def test_api_startup_records_and_logs_schema_failure(self) -> None:
        record_schema_startup_success(datetime.now(timezone.utc))
        self.addCleanup(lambda: record_schema_startup_success(datetime.now(timezone.utc)))

        with patch("app.api.server.ensure_schema", side_effect=RuntimeError("schema migration failed")), self.assertLogs(
            "energy_monitoring.api.server", level="ERROR"
        ) as captured:
            api_server.create_app()

        schema_state = get_schema_startup_state()
        self.assertEqual(schema_state["status"], "degraded")
        self.assertEqual(schema_state["lastErrorType"], "RuntimeError")
        self.assertEqual(schema_state["lastErrorMessage"], "schema migration failed")
        self.assertTrue(any("Database schema startup check failed" in message for message in captured.output))

    def test_system_health_reports_schema_startup_failure_as_degraded(self) -> None:
        failure = RuntimeError("schema migration failed")
        record_schema_startup_failure(failure, datetime(2026, 7, 31, 10, 30, tzinfo=timezone.utc))
        self.addCleanup(lambda: record_schema_startup_success(datetime.now(timezone.utc)))

        settings = SimpleNamespace(
            enable_database=True,
            demo_mode=False,
            poll_interval_seconds=180,
            reading_spool_path=":memory:",
            reading_spool_max_rows=100,
            reading_spool_max_rows_per_meter=10,
            reading_spool_retention_days=30,
        )

        class FakeReadingSpool:
            def __init__(self, *args, **kwargs) -> None:
                return None

            def status(self):
                return {
                    "queuedCount": 0,
                    "maxQueueSize": 100,
                    "maxQueueSizePerMeter": 10,
                    "retentionDays": 30,
                    "oldestQueuedAt": "",
                    "lastReplayAt": "",
                    "lastReplayError": "",
                }

        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def execute(self, query, params=None) -> None:
                return None

            def fetchone(self):
                return {"ok": 1}

        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def cursor(self):
                return FakeCursor()

        healthy_hardening = api_service._default_database_hardening_status()
        healthy_hardening.update(
            {
                "readingsPartitioned": True,
                "readingsIdDefaultPresent": True,
                "hourlyAggregateRows": 1,
            }
        )

        with patch("app.api.service.get_runtime_settings", return_value=settings), patch(
            "app.api.service.get_polling_settings",
            return_value={"pollIntervalSeconds": 180, "updatedAt": "", "source": "environment"},
        ), patch("app.api.service.ReadingSpool", FakeReadingSpool), patch(
            "app.api.service._open_connection",
            return_value=FakeConnection(),
        ), patch(
            "app.api.service._database_hardening_status",
            return_value=healthy_hardening,
        ), patch(
            "app.api.service.list_meters",
            return_value=[],
        ):
            health = api_service.get_system_health()

        self.assertEqual(health["status"], "degraded")
        self.assertEqual(health["databaseStatus"], "degraded")
        self.assertEqual(health["schemaStartup"]["status"], "degraded")
        self.assertEqual(health["checks"]["schemaStartup"]["status"], "degraded")
        self.assertIn("schema migration failed", health["checks"]["schemaStartup"]["message"])
