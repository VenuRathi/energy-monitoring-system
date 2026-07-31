import unittest
from types import SimpleNamespace
from unittest.mock import patch

from config.meter_loader import load_meter_config
from main import build_runtime_meter_definition, load_runtime_meters


class RuntimeMeterDefinitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.meter_config = load_meter_config()

    def test_unknown_meter_id_uses_matching_driver_template(self) -> None:
        runtime_definition = build_runtime_meter_definition(
            {
                "meter_id": "MTR-999",
                "meter_name": "New Meter",
                "location": "Panel-9",
                "enabled": True,
                "driver": "schneider.pm5000",
                "com_port": "COM9",
                "slave_id": 9,
                "baud_rate": 9600,
                "parity": "N",
                "stop_bits": 1,
                "byte_size": 8,
                "timeout": 2.0,
                "one_based_map": True,
            },
            self.meter_config,
        )

        self.assertEqual(runtime_definition["meter_id"], "MTR-999")
        self.assertEqual(runtime_definition["driver"], "schneider.pm5000")
        self.assertEqual(runtime_definition["connection"]["port"], "COM9")
        self.assertEqual(runtime_definition["connection"]["slave_id"], 9)
        self.assertEqual(runtime_definition["meter_timestamp_parameter"], "Present Date & Time")
        self.assertGreater(len(runtime_definition["parameters"]), 0)

    def test_unknown_driver_raises_clear_error(self) -> None:
        with self.assertRaises(ValueError):
            build_runtime_meter_definition(
                {
                    "meter_id": "MTR-998",
                    "meter_name": "Unsupported Meter",
                    "location": "Panel-X",
                    "enabled": True,
                    "driver": "custom.driver",
                    "com_port": "COM8",
                    "slave_id": 8,
                    "baud_rate": 9600,
                    "parity": "N",
                    "stop_bits": 1,
                    "byte_size": 8,
                    "timeout": 2.0,
                    "one_based_map": True,
                },
                self.meter_config,
            )

    def test_runtime_loader_refreshes_from_enabled_database_meters_only(self) -> None:
        class FakeMeterRepository:
            def __init__(self, settings) -> None:
                self.settings = settings

            def list_meters(self):
                return [
                    {
                        "meter_id": "MTR-ENABLED",
                        "meter_name": "Enabled Meter",
                        "location": "Panel A",
                        "enabled": True,
                        "driver": "schneider.pm5000",
                        "com_port": "COM8",
                        "slave_id": 8,
                        "baud_rate": 19200,
                        "parity": "E",
                        "stop_bits": 2,
                        "byte_size": 7,
                        "timeout": 3.5,
                        "one_based_map": False,
                    },
                    {
                        "meter_id": "MTR-DISABLED",
                        "meter_name": "Disabled Meter",
                        "location": "Panel B",
                        "enabled": False,
                        "driver": "schneider.pm5000",
                        "com_port": "COM9",
                        "slave_id": 9,
                        "baud_rate": 9600,
                        "parity": "N",
                        "stop_bits": 1,
                        "byte_size": 8,
                        "timeout": 2.0,
                        "one_based_map": True,
                    },
                ]

        settings = SimpleNamespace(enable_database=True)
        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback) -> None:
                return None

            def close(self) -> None:
                return None

        with patch("main.get_connection", return_value=FakeConnection()), patch("main.MeterRepository", FakeMeterRepository):
            runtime_meters = load_runtime_meters(settings, self.meter_config)

        self.assertEqual([meter["meter_id"] for meter in runtime_meters], ["MTR-ENABLED"])
        connection = runtime_meters[0]["connection"]
        self.assertEqual(connection["port"], "COM8")
        self.assertEqual(connection["slave_id"], 8)
        self.assertEqual(connection["baud_rate"], 19200)
        self.assertEqual(connection["parity"], "E")
        self.assertEqual(connection["stop_bits"], 2)
        self.assertEqual(connection["byte_size"], 7)
        self.assertEqual(connection["timeout"], 3.5)
        self.assertFalse(connection["one_based_map"])
