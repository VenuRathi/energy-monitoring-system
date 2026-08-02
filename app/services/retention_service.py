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
        if (
            hasattr(self.reading_repository, "readings_table_is_partitioned")
            and self.reading_repository.readings_table_is_partitioned()
        ):
            if hasattr(self.reading_repository, "ensure_daily_reading_partitions"):
                self.reading_repository.ensure_daily_reading_partitions(days_back=1, days_ahead=7)
            removed_count = self.reading_repository.drop_old_daily_reading_partitions(retention_days)
            removal_unit = "partition(s)"
        else:
            removed_count = self.reading_repository.delete_readings_older_than(
                cutoff=cutoff,
                limit=max(1, int(self.settings.readings_cleanup_batch_size)),
            )
            removal_unit = "row(s)"

        if removed_count > 0:
            logger.info(
                "Readings retention removed %s %s older than %s.",
                removed_count,
                removal_unit,
                cutoff.isoformat(),
            )
        return removed_count
