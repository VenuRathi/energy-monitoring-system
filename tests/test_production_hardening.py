import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from threading import Event
from types import SimpleNamespace

from app.services.polling_service import PollingService
from app.services.reading_spool import ReadingSpool
from app.services.report_worker import ReportWorker


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
