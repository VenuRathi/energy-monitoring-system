import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from app.runtime_state import get_all_meter_runtime_statuses
from app.services.polling_service import PollingService
from app.services.buffered_reading_repository import BufferedReadingRepository
from app.services.reading_spool import ReadingSpool
from app.services.report_worker import ReportWorker
from main import _validate_shared_bus_settings


class ReadingSpoolTests(unittest.TestCase):
    def make_spool(self) -> ReadingSpool:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return ReadingSpool(Path(directory.name) / "spool.sqlite3", retention_days=30)

    @staticmethod
    def reading_timestamp(second: int) -> datetime:
        return datetime(2026, 7, 24, 10, 0, second)

    def test_replay_success_removes_queued_reading(self) -> None:
        spool = self.make_spool()
        timestamp = self.reading_timestamp(1)
        self.assertTrue(
            spool.enqueue(
                meter_id="MTR-001",
                timestamp=timestamp,
                readings={"Active Power Total": 12.5},
                collected_at=timestamp,
                timestamp_source="collector_fallback",
            )
        )

        replayed = []
        result = spool.replay({"MTR-001": lambda reading: replayed.append(reading) or True})

        self.assertEqual(result, {"replayed": 1, "duplicates": 0, "failed": 0})
        self.assertEqual(len(replayed), 1)
        self.assertEqual(spool.status()["queuedCount"], 0)

    def test_duplicate_enqueue_and_duplicate_replay_are_safe(self) -> None:
        spool = self.make_spool()
        timestamp = self.reading_timestamp(2)
        kwargs = {
            "meter_id": "MTR-001",
            "timestamp": timestamp,
            "readings": {"Frequency": 50.0},
            "collected_at": timestamp,
            "timestamp_source": "meter",
        }
        self.assertTrue(spool.enqueue(**kwargs))
        self.assertFalse(spool.enqueue(**kwargs))

        result = spool.replay({"MTR-001": lambda reading: False})

        self.assertEqual(result, {"replayed": 0, "duplicates": 1, "failed": 0})
        self.assertEqual(spool.status()["queuedCount"], 0)

    def test_failed_meter_does_not_block_other_meter_recovery(self) -> None:
        spool = self.make_spool()
        for meter_id, second in (("MTR-001", 3), ("MTR-002", 4)):
            spool.enqueue(
                meter_id=meter_id,
                timestamp=self.reading_timestamp(second),
                readings={"Frequency": 50.0},
                timestamp_source="meter",
            )

        def fail_meter_one(reading):
            if reading.meter_id == "MTR-001":
                raise RuntimeError("database still unavailable")
            return True

        result = spool.replay({"MTR-001": fail_meter_one, "MTR-002": fail_meter_one})

        self.assertEqual(result["replayed"], 1)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(spool.status()["queuedCount"], 1)
        self.assertIn("MTR-001", spool.status()["lastReplayError"])

    def test_database_insert_failure_queues_reading(self) -> None:
        class FailingReadingRepository:
            def insert_reading(self, **kwargs):
                raise RuntimeError("database unavailable")

        spool = self.make_spool()
        service = PollingService(
            meter_config={
                "meter_id": "MTR-001",
                "meter_name": "Test Meter",
                "parameters": [{"name": "Frequency", "type": "float32"}],
                "connection": {"com_port": "COM5", "slave_id": 1},
            },
            collector=None,
            poll_interval_seconds=18,
            reading_repository=FailingReadingRepository(),
            reading_spool=spool,
        )

        timestamp = self.reading_timestamp(5)
        service._save_database(
            reading_timestamp=timestamp,
            collected_at=timestamp,
            reading_date="24/07/2026",
            reading_time="10:00:05",
            timestamp_source="collector_fallback",
            meter_timestamp=None,
            readings={"Frequency": 50.0},
        )

        self.assertEqual(spool.status()["queuedCount"], 1)
        replayed = []
        result = spool.replay({"MTR-001": lambda reading: replayed.append(reading) or True})
        self.assertEqual(result, {"replayed": 1, "duplicates": 0, "failed": 0})
        self.assertEqual(replayed[0].readings["Frequency"], 50.0)

    def test_buffered_write_failure_queues_entire_batch(self) -> None:
        class FailingRepository:
            def insert_readings(self, payloads):
                raise RuntimeError("postgres unavailable")

        spool = self.make_spool()
        buffered = BufferedReadingRepository(
            FailingRepository(),
            reading_spool=spool,
            max_rows=2,
            max_seconds=60,
        )

        for second in (6, 7):
            buffered.insert_reading(
                meter_id="MTR-001",
                timestamp=self.reading_timestamp(second),
                readings={"Frequency": 50.0 + second},
                timestamp_source="meter",
            )

        self.assertEqual(spool.status()["queuedCount"], 2)

    def test_spool_replay_uses_immediate_insert_when_available(self) -> None:
        class BufferedLikeRepository:
            def __init__(self) -> None:
                self.buffered_calls = 0
                self.immediate_calls = 0
                self.flush_calls = 0

            def insert_reading(self, **kwargs):
                self.buffered_calls += 1
                return True

            def insert_reading_immediate(self, **kwargs):
                self.immediate_calls += 1
                return True

            def flush(self):
                self.flush_calls += 1
                return 0

        repository = BufferedLikeRepository()
        service = PollingService(
            meter_config={
                "meter_id": "MTR-001",
                "meter_name": "Test Meter",
                "parameters": [{"name": "Frequency", "type": "float32"}],
                "connection": {"com_port": "COM5", "slave_id": 1},
            },
            collector=None,
            poll_interval_seconds=18,
            reading_repository=repository,
        )

        queued = type(
            "Queued",
            (),
            {
                "meter_id": "MTR-001",
                "timestamp": self.reading_timestamp(8),
                "readings": {"Frequency": 50.0},
                "meter_timestamp": None,
                "collected_at": self.reading_timestamp(8),
                "reading_date": "24/07/2026",
                "reading_time": "10:00:08",
                "timestamp_source": "meter",
            },
        )()

        self.assertTrue(service.replay_queued_reading(queued))
        self.assertEqual(repository.immediate_calls, 1)
        self.assertEqual(repository.buffered_calls, 0)
        self.assertEqual(repository.flush_calls, 0)


class MeterClockTests(unittest.TestCase):
    def make_service(self, drift_seconds: int = 120) -> PollingService:
        return PollingService(
            meter_config={
                "meter_id": "MTR-001",
                "meter_timestamp_parameter": "Present Date & Time",
                "parameters": [
                    {"name": "Present Date & Time", "type": "datetime4"},
                ],
            },
            collector=None,
            poll_interval_seconds=18,
            meter_clock_max_drift_seconds=drift_seconds,
        )

    def test_valid_meter_clock_is_used(self) -> None:
        service = self.make_service()
        collected_at = datetime(2026, 6, 26, 14, 48, 19, 506000, tzinfo=service.app_timezone)

        timestamp, source, raw_timestamp = service._resolve_meter_timestamp(
            {"Present Date & Time": "001A-061A-0E30-4C32"},
            collected_at,
        )

        self.assertEqual(source, "meter")
        self.assertEqual(timestamp, collected_at)
        self.assertEqual(raw_timestamp, collected_at)

    def test_future_and_old_meter_clocks_are_rejected(self) -> None:
        service = self.make_service(drift_seconds=60)
        collected_at = datetime(2026, 6, 26, 14, 48, 19, 506000, tzinfo=service.app_timezone)

        for raw_value in ("001A-061A-1030-4C32", "001A-061A-0030-4C32"):
            timestamp, source, raw_timestamp = service._resolve_meter_timestamp(
                {"Present Date & Time": raw_value},
                collected_at,
            )
            self.assertIsNone(timestamp)
            self.assertEqual(source, "meter_rejected")
            self.assertIsNotNone(raw_timestamp)

    def test_invalid_and_missing_meter_clocks_use_collector_time(self) -> None:
        service = self.make_service()
        collected_at = datetime(2026, 6, 26, 14, 48, 19, 506000, tzinfo=service.app_timezone)

        for readings, expected_source in (
            ({"Present Date & Time": "invalid"}, "meter_rejected"),
            ({"Present Date & Time": None}, "collector_fallback"),
            ({}, "collector_fallback"),
        ):
            timestamp, source, raw_timestamp = service._resolve_meter_timestamp(readings, collected_at)
            self.assertIsNone(timestamp)
            self.assertEqual(source, expected_source)
            self.assertIsNone(raw_timestamp)


class ReportWorkerTests(unittest.TestCase):
    def test_slow_report_work_runs_off_the_calling_thread(self) -> None:
        stop_event = Event()
        started = Event()
        release = Event()

        def slow_report_work():
            started.set()
            release.wait(2)
            return []

        settings = SimpleNamespace(report_worker_interval_seconds=1)
        worker = ReportWorker(settings, stop_event, process_function=slow_report_work)
        worker.start()
        self.addCleanup(lambda: (release.set(), stop_event.set(), worker.join(timeout=3)))

        self.assertTrue(started.wait(2))
        polling_start = time.monotonic()
        polling_result = "polling thread remained available"
        self.assertLess(time.monotonic() - polling_start, 0.1)
        self.assertEqual(polling_result, "polling thread remained available")


class MeterDiagnosticsTests(unittest.TestCase):
    @staticmethod
    def meter_definition(meter_id: str, *, com_port: str = "COM5", slave_id: int = 1, baud_rate: int = 9600) -> dict:
        return {
            "meter_id": meter_id,
            "meter_name": meter_id,
            "manufacturer": "Schneider",
            "model": "PM5000-EM6400",
            "location": "Panel",
            "protocol": "modbus_rtu",
            "enabled": True,
            "parameters": [{"name": "Frequency", "type": "float32"}],
            "connection": {
                "com_port": com_port,
                "port": com_port,
                "slave_id": slave_id,
                "baud_rate": baud_rate,
                "parity": "N",
                "stop_bits": 1,
                "byte_size": 8,
                "timeout": 2.0,
            },
        }

    def test_missing_configured_com_port_is_visible_but_meter_still_retries(self) -> None:
        meters = [self.meter_definition("PH4-MISSING-COM", com_port="COM42")]

        with patch("main._available_com_ports", return_value={"COM5"}):
            valid = _validate_shared_bus_settings(meters, logger=SimpleNamespace(warning=lambda *args, **kwargs: None))

        self.assertEqual(valid, meters)
        state = get_all_meter_runtime_statuses()["PH4-MISSING-COM"]
        self.assertEqual(state["diagnosticCode"], "com_port_missing")
        self.assertIn("COM port missing", state["diagnosticMessage"])
        self.assertEqual(state["communicationStatus"], "warning")

    def test_duplicate_slave_id_is_classified_without_blocking_good_meter(self) -> None:
        meters = [
            self.meter_definition("PH4-DUP-GOOD", slave_id=1),
            self.meter_definition("PH4-DUP-BAD", slave_id=1),
        ]

        with patch("main._available_com_ports", return_value={"COM5"}):
            valid = _validate_shared_bus_settings(meters, logger=SimpleNamespace(warning=lambda *args, **kwargs: None))

        self.assertEqual([meter["meter_id"] for meter in valid], ["PH4-DUP-GOOD"])
        state = get_all_meter_runtime_statuses()["PH4-DUP-BAD"]
        self.assertEqual(state["diagnosticCode"], "duplicate_slave_id")
        self.assertIn("Duplicate slave ID", state["diagnosticMessage"])

    def test_serial_settings_conflict_is_classified_without_blocking_good_meter(self) -> None:
        meters = [
            self.meter_definition("PH4-SERIAL-GOOD", baud_rate=9600),
            self.meter_definition("PH4-SERIAL-BAD", slave_id=2, baud_rate=19200),
        ]

        with patch("main._available_com_ports", return_value={"COM5"}):
            valid = _validate_shared_bus_settings(meters, logger=SimpleNamespace(warning=lambda *args, **kwargs: None))

        self.assertEqual([meter["meter_id"] for meter in valid], ["PH4-SERIAL-GOOD"])
        state = get_all_meter_runtime_statuses()["PH4-SERIAL-BAD"]
        self.assertEqual(state["diagnosticCode"], "serial_settings_conflict")
        self.assertIn("Serial settings conflict", state["diagnosticMessage"])

    def test_no_readings_is_classified_as_meter_no_response(self) -> None:
        class EmptyCollector:
            def read_all(self):
                return {"Frequency": None}

        service = PollingService(
            meter_config=self.meter_definition("PH4-NO-RESPONSE"),
            collector=EmptyCollector(),
            poll_interval_seconds=18,
        )

        service.poll_once()

        state = get_all_meter_runtime_statuses()["PH4-NO-RESPONSE"]
        self.assertEqual(state["diagnosticCode"], "meter_no_response")
        self.assertIn("Meter no response", state["diagnosticMessage"])
