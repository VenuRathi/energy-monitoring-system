import json
import tempfile
import unittest
from pathlib import Path

from config.meter_loader import load_meter_config


class LoadMeterConfigTests(unittest.TestCase):
    def write_config(self, payload: dict) -> Path:
        temp_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with temp_file:
            json.dump(payload, temp_file)
        self.addCleanup(lambda: Path(temp_file.name).unlink(missing_ok=True))
        return Path(temp_file.name)

    def test_expands_defaults_and_parameter_sets(self) -> None:
        config_path = self.write_config(
            {
                "meter_defaults": {
                    "manufacturer": "Schneider",
                    "model": "PM5000-EM6400",
                    "protocol": "modbus_rtu",
                    "enabled": True,
                    "driver": "schneider.pm5000",
                },
                "connection_defaults": {
                    "baud_rate": 9600,
                    "parity": "N",
                    "stop_bits": 1,
                    "byte_size": 8,
                    "timeout": 2.0,
                    "one_based_map": True,
                },
                "parameter_sets": {
                    "core": [
                        {"name": "Voltage L-N Avg", "register": 3036, "type": "float32", "unit": "V", "scale": 1.0}
                    ]
                },
                "meters": [
                    {
                        "meter_id": "MTR-101",
                        "meter_name": "Test Meter",
                        "location": "Panel-1",
                        "parameter_set": "core",
                        "connection": {"port": "COM6", "slave_id": 1},
                    }
                ],
            }
        )

        config = load_meter_config(str(config_path))
        meter = config["meters"][0]

        self.assertEqual(meter["manufacturer"], "Schneider")
        self.assertEqual(meter["driver"], "schneider.pm5000")
        self.assertEqual(meter["connection"]["baud_rate"], 9600)
        self.assertEqual(meter["connection"]["port"], "COM6")
        self.assertEqual(meter["parameters"][0]["name"], "Voltage L-N Avg")

    def test_rejects_inline_parameters_and_parameter_set(self) -> None:
        config_path = self.write_config(
            {
                "parameter_sets": {
                    "core": [
                        {"name": "Voltage L-N Avg", "register": 3036, "type": "float32", "unit": "V", "scale": 1.0}
                    ]
                },
                "meters": [
                    {
                        "meter_id": "MTR-ERR",
                        "meter_name": "Invalid Meter",
                        "location": "Panel-X",
                        "parameter_set": "core",
                        "parameters": [
                            {"name": "Current Avg", "register": 3010, "type": "float32", "unit": "A", "scale": 1.0}
                        ],
                    }
                ],
            }
        )

        with self.assertRaises(ValueError):
            load_meter_config(str(config_path))
