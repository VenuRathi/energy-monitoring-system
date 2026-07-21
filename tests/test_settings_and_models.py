import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.database.connection import get_connection
from app.database.models import validate_parameter_columns
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

    def test_validate_parameter_columns_rejects_collisions(self) -> None:
        parameters = [
            {"name": "Power Factor (Total)", "type": "float32"},
            {"name": "Power Factor Total", "type": "float32"},
        ]

        with self.assertRaises(ValueError):
            validate_parameter_columns(parameters)

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
                "API_DEBUG": "false",
            },
            clear=False,
        ):
            settings = load_settings()

        self.assertEqual(settings.readings_retention_days, 365)
        self.assertEqual(settings.readings_cleanup_batch_size, 123)
        self.assertEqual(settings.readings_cleanup_interval_hours, 6)

    def test_retention_service_uses_configured_cutoff_and_batch(self) -> None:
        class FakeReadingRepository:
            def __init__(self) -> None:
                self.cutoff = None
                self.limit = None

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

    def test_duplicate_reading_is_skipped_before_insert(self) -> None:
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
        inserted = ReadingRepository(connection=connection, parameters=[]).insert_reading(
            meter_id="MTR-001",
            timestamp=datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc),
            readings={},
            timestamp_source="meter",
        )

        self.assertFalse(inserted)
        self.assertFalse(connection.committed)
        self.assertEqual(len(connection.cursor_instance.executed_sql), 1)
        self.assertIn("SELECT 1", connection.cursor_instance.executed_sql[0])

    def test_new_reading_is_inserted_and_committed(self) -> None:
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
                return None

        class FakeConnection:
            def __init__(self) -> None:
                self.cursor_instance = FakeCursor()
                self.committed = False

            def cursor(self):
                return self.cursor_instance

            def commit(self) -> None:
                self.committed = True

        connection = FakeConnection()
        inserted = ReadingRepository(connection=connection, parameters=[]).insert_reading(
            meter_id="MTR-001",
            timestamp=datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc),
            readings={},
            timestamp_source="meter",
        )

        self.assertTrue(inserted)
        self.assertTrue(connection.committed)
        self.assertEqual(len(connection.cursor_instance.executed_sql), 2)
        self.assertIn("INSERT INTO readings", connection.cursor_instance.executed_sql[1])

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
