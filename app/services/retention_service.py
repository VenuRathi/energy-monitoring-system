from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.database.repositories import ReadingRepository
from config.settings import Settings


logger = logging.getLogger("energy_monitoring.retention_service")


class ReadingsRetentionService:
    def __init__(self, settings: Settings, reading_repository: ReadingRepository) -> None:
        self.settings = settings
        self.reading_repository = reading_repository

    def cleanup_once(self, now: datetime | None = None) -> int:
        retention_days = int(self.settings.readings_retention_days)
        if retention_days <= 0:
            return 0

        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        cutoff = current_time.astimezone(timezone.utc) - timedelta(days=retention_days)
        deleted_count = self.reading_repository.delete_readings_older_than(
            cutoff=cutoff,
            limit=max(1, int(self.settings.readings_cleanup_batch_size)),
        )
        if deleted_count > 0:
            logger.info(
                "Readings retention removed %s row(s) older than %s.",
                deleted_count,
                cutoff.isoformat(),
            )
        return deleted_count
