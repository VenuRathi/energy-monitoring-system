import os
import unittest
from unittest.mock import patch

from app.database.models import validate_parameter_columns
from app.services.polling_service import PollingService
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
            settings.cors_allowed_origins,
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
