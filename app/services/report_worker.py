from __future__ import annotations

import logging
from threading import Event, Thread
from typing import Callable

from app.api.service import process_due_report_schedules
from config.settings import Settings


logger = logging.getLogger("energy_monitoring.report_worker")


class ReportWorker:
    """Runs scheduled report/email work independently from meter polling."""

    def __init__(
        self,
        settings: Settings,
        stop_event: Event,
        process_function: Callable[[], list[dict]] = process_due_report_schedules,
    ) -> None:
        self.settings = settings
        self.stop_event = stop_event
        self.process_function = process_function
        self._thread = Thread(target=self._run, name="scheduled-report-worker", daemon=True)

    def start(self) -> None:
        self._thread.start()
        logger.info(
            "Scheduled report worker started with interval %ss.",
            self.settings.report_worker_interval_seconds,
        )

    def join(self, timeout: float | None = None) -> None:
        self._thread.join(timeout=timeout)

    def _run(self) -> None:
        interval = max(1, int(self.settings.report_worker_interval_seconds))
        while not self.stop_event.wait(interval):
            try:
                results = self.process_function()
                if results:
                    logger.info("Scheduled report worker completed %s report operation(s).", len(results))
            except Exception:
                logger.exception("Scheduled report worker failed.")
        logger.info("Scheduled report worker stopped.")
