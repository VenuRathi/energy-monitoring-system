import unittest

from config.meter_loader import load_meter_config
from main import build_runtime_meter_definition


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
