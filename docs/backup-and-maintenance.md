# Backup and Maintenance

This is the minimum practical maintenance guidance for the pilot.

## PostgreSQL backup recommendation

For a pilot, use:

- daily logical backup
- weekly retention review

Recommended script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup_postgres.ps1
```

What it does:

- reads `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` from `.env`
- creates a timestamped `.dump` file in `backups\`
- keeps recent dumps and removes older ones based on retention days

Optional daily backup task install:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_daily_backup_task.ps1
```

After installing the backup task, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\post_install_check.ps1
```

The post-install check reports whether the backend and daily backup scheduled tasks are visible.

Optional example with explicit retention:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup_postgres.ps1 -RetentionDays 14
```

## Minimum backup recommendation

- Daily backup of PostgreSQL database
- Weekly copy of the project `.env`
- Weekly copy of `config/` and any deployment scripts/docs
- occasional release snapshot using [release-bundle.md](release-bundle.md)

## Database size check

```sql
SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size;
```

## Database hardening verification

After partition migration, hourly aggregate setup, or PostgreSQL tuning changes, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_database_hardening.ps1
```

This checks:

- `readings` is partitioned
- raw reading row count and time range
- partition count
- duplicate groups
- hourly aggregate row count and time range
- important PostgreSQL tuning values
- whether restart-level settings are applied

## Latest readings check

```sql
SELECT DISTINCT ON (meter_id)
    meter_id,
    collected_at,
    timestamp
FROM readings
ORDER BY meter_id, collected_at DESC;
```

## Row counts per meter

```sql
SELECT meter_id, COUNT(*) AS reading_count
FROM readings
GROUP BY meter_id
ORDER BY meter_id;
```

## Readings retention

The backend supports automatic readings retention for long-running installations.

Production behavior after `readings` is migrated to daily partitions:

- old daily partitions are dropped
- PostgreSQL immediately releases the partition table and index files
- no row-by-row `DELETE` is needed
- table and index bloat from retention cleanup is avoided

Default behavior:

- `READINGS_RETENTION_DAYS=1825`
- `READINGS_CLEANUP_BATCH_SIZE=5000`
- `READINGS_CLEANUP_INTERVAL_HOURS=1`

This keeps about five years of readings by default. Cleanup runs after normal polling/report work, not during startup. On partitioned databases it drops old partitions. On pre-migration databases it falls back to the older bounded-delete behavior.

To disable automatic cleanup during an initial supervised pilot:

```env
READINGS_RETENTION_DAYS=0
```

Before reducing retention below five years, confirm the factory/reporting requirement and take a PostgreSQL backup.

## Partition migration

Existing databases created before partitioning must be migrated once:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup_postgres.ps1
```

Then run the duplicate check below. If it returns no rows, stop the backend service and run:

```sql
\i sql/migrate_readings_to_daily_partitions.sql
```

Keep `readings_legacy` for supervised validation, then drop it manually after confirming row counts, latest readings, dashboards, and reports.

After several days of clean operation, take a fresh backup and remove the legacy table with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\drop_readings_legacy_after_validation.ps1 -ConfirmDrop
```

The script refuses to run unless `-ConfirmDrop` is passed, and it checks that `readings_legacy` and `readings` have matching row counts before dropping the legacy table.

## Duplicate reading handling

The backend now relies on PostgreSQL duplicate protection using:

- `meter_id`
- `timestamp`
- `timestamp_source`

New inserts use `ON CONFLICT DO NOTHING`. Before migration or before adding the unique index to an existing legacy table, inspect historical rows for duplicates and clean them first.

Suggested duplicate check:

```sql
SELECT meter_id, timestamp, timestamp_source, COUNT(*) AS duplicates
FROM readings
GROUP BY meter_id, timestamp, timestamp_source
HAVING COUNT(*) > 1
ORDER BY duplicates DESC, timestamp DESC;
```

## Log maintenance

Current backend log behavior:

- writes to `logs/energy_monitoring.log`
- rotates at roughly 5 MB
- keeps 7 backups

Check occasionally:

- disk usage
- repeated COM or meter warnings
- repeated database failures

## Weekly maintenance checklist

- review `/api/status`
- check latest readings in PostgreSQL
- check database size
- confirm scheduled task is still enabled
- confirm backup files are being created
