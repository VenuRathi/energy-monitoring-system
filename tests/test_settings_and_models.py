import os
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
from types import SimpleNamespace

from app.database.connection import get_connection
from app.database.models import build_readings_table_sql, create_tables, validate_parameter_columns
from app.database.repositories import ReadingRepository
from app.services.retention_service import ReadingsRetentionService
from app.services.polling_service import PollingService
from app.api import server as api_server
from app.api import service as api_service
from config.settings import load_settings


class SettingsAndModelsTests(unittest.TestCase):
    def test_settings_parse_allowed_origins(self) -> None:
        with patch.dict(
            os.environ,
            {
                "CORS_ALLOWED_ORIGINS": "http://127.0.0.1:5173, http://localhost:5173",
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
        ddl = build_readings_table_sql([{"name": "Frequency", "type": "float32"}])

        self.assertIn("PARTITION BY RANGE (timestamp)", ddl)
        self.assertIn("PRIMARY KEY (timestamp, id)", ddl)
        self.assertIn("UNIQUE (meter_id, timestamp, timestamp_source)", ddl)
        self.assertIn("frequency DOUBLE PRECISION", ddl)

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

        original_exists = Path.exists
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
