# Backup and Maintenance

This is the minimum practical maintenance guidance for the pilot.

## PostgreSQL backup recommendation

For a pilot, use:

- daily logical backup
- weekly retention review

Example daily backup command:

```powershell
pg_dump -h 127.0.0.1 -U postgres -d energy_monitoring -F c -f C:\EnergyMonitoring\backups\energy_monitoring_%DATE%.dump
```

Use a backup filename pattern suitable for your Windows locale or wrap it in a scheduled script.

## Minimum backup recommendation

- Daily backup of PostgreSQL database
- Weekly copy of the project `.env`
- Weekly copy of `config/` and any deployment scripts/docs

## Database size check

```sql
SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size;
```

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

## Retention recommendation

Do not auto-delete data during the initial pilot.

Recommended pilot approach:

- keep all readings during the pilot
- review database growth after 2-4 weeks
- then decide whether to archive old data monthly or quarterly

At 4-5 meters with 3-minute polling, the current schema should be acceptable for the pilot window.

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
