import io
import unittest
from datetime import datetime, timezone

from openpyxl import load_workbook

from app.api import service
from app.collectors.schneider.pm5000 import PM5000Collector
from app.database.models import parameter_name_to_column_name
from app.database.repositories import ReadingRepository
from config.meter_loader import load_meter_config


class EnergyMeteringTests(unittest.TestCase):
    def test_config_uses_delivered_import_four_register_int64_counters(self) -> None:
        config = load_meter_config()
        parameters = {
            parameter["name"]: parameter
            for parameter in config["meters"][0]["parameters"]
        }

        expected = {
            "Active Energy Delivered / Import": (3204, "int64", "kWh", 0.001),
            "Reactive Energy Delivered / Import": (3220, "int64", "kVARh", 0.001),
            "Apparent Energy Delivered / Import": (3236, "int64", "kVAh", 0.001),
        }
        for name, (register, data_type, unit, scale) in expected.items():
            with self.subTest(name=name):
                parameter = parameters[name]
                self.assertEqual(parameter["register"], register)
                self.assertEqual(parameter["type"], data_type)
                self.assertEqual(parameter["unit"], unit)
                self.assertEqual(parameter["scale"], scale)

        self.assertEqual(
            parameter_name_to_column_name("Active Energy Delivered / Import"),
            "active_energy_received_out_of_load",
        )
        self.assertEqual(
            parameter_name_to_column_name("Reactive Energy Delivered / Import"),
            "reactive_energy_received",
        )
        self.assertEqual(
            parameter_name_to_column_name("Apparent Energy Delivered / Import"),
            "apparent_energy_received",
        )

    def test_int64_uses_schneider_register_list_word_order(self) -> None:
        collector = PM5000Collector(
            modbus_client=None,
            parameters=[],
            slave_id=1,
            meter_id="MTR-001",
        )
        registers = [0x1234, 0x9ABC, 0xDEF0, 0x5678]

        decoded = collector._read_int64_lsw(3204, {"blocks": [(3204, registers)]})

        self.assertEqual(decoded, 0x12349ABCDEF05678)
        self.assertEqual(collector._word_count_for_type("int64"), 4)

    def test_int64_decodes_the_meter_values_without_high_word_overflow(self) -> None:
        collector = PM5000Collector(
            modbus_client=None,
            parameters=[],
            slave_id=1,
            meter_id="MTR-001",
        )

        decoded = collector._read_int64_lsw(
            3204,
            {"blocks": [(3204, [0x0000, 0x0000, 0x00CB, 0xB66C])]},
        )

        self.assertEqual(decoded, 13_350_508)

    def test_daily_delta_uses_cumulative_today_minus_yesterday(self) -> None:
        delta, status = service.calculate_daily_energy_delta(1250.5, 1000.25)

        self.assertEqual(delta, 250.25)
        self.assertIsNone(status)

        reactive_delta, reactive_status = service.calculate_daily_energy_delta(-15872.699, -15872.702)
        self.assertAlmostEqual(reactive_delta, 0.003, places=9)
        self.assertIsNone(reactive_status)

    def test_reading_persistence_keeps_cumulative_values(self) -> None:
        parameters = [
            {"name": "Active Energy Delivered / Import", "type": "int64"},
            {"name": "Reactive Energy Delivered / Import", "type": "int64"},
            {"name": "Apparent Energy Delivered / Import", "type": "int64"},
        ]
        repository = ReadingRepository(parameters=parameters)

        values = repository._insert_values(
            {
                "meter_id": "MTR-001",
                "timestamp": datetime(2026, 8, 21, tzinfo=timezone.utc),
                "readings": {
                    "Active Energy Delivered / Import": 123456.789,
                    "Reactive Energy Delivered / Import": 4567.891,
                    "Apparent Energy Delivered / Import": 789012.346,
                },
            }
        )

        self.assertEqual(values[-3:], [123456.789, 4567.891, 789012.346])

    def test_counter_reset_is_not_reported_as_negative_usage(self) -> None:
        delta, status = service.calculate_daily_energy_delta(12.0, 9876.0)

        self.assertIsNone(delta)
        self.assertEqual(status, "RESET/INVALID: CUMULATIVE COUNTER DECREASED")

    def test_scheduled_report_cell_flags_reset_instead_of_writing_negative_formula(self) -> None:
        parameter_key = "active_energy_received_out_of_load"
        previous = {
            "timestamp": datetime(2026, 8, 20, 18, 0, tzinfo=timezone.utc),
            parameter_key: 9876.0,
        }
        current = service._annotate_daily_energy_deltas(
            "MTR-001",
            [previous, {
                "timestamp": datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
                parameter_key: 12.0,
            }],
            [parameter_key],
        )[-1]

        meter = {"meter_id": "MTR-001", "meter_name": "Test Meter"}
        report_bytes = service._build_scheduled_excel_bytes(
            [(meter, [current])],
            [parameter_key],
            "23:59",
        )
        workbook = load_workbook(filename=io.BytesIO(report_bytes), data_only=False)

        self.assertEqual(workbook.active.cell(row=3, column=4).value, "RESET/INVALID: CUMULATIVE COUNTER DECREASED")
