# Production Readiness And Signoff Checklist

Current readiness state:

```text
Production-ready with conditions
```

The code has the major hardening needed for a controlled plant deployment, but final production signoff still requires field evidence and operational proof.

## Completed Technical Hardening

- [x] Runtime health endpoint available at `/api/status`.
- [x] Per-meter online/warning/offline state available.
- [x] PostgreSQL persistence active.
- [x] Database connection timeout configured with `DB_CONNECT_TIMEOUT_SECONDS`.
- [x] Readings retention configured with `READINGS_RETENTION_DAYS`.
- [x] Retention cleanup is bounded by `READINGS_CLEANUP_BATCH_SIZE`.
- [x] Retention cleanup is throttled by `READINGS_CLEANUP_INTERVAL_HOURS`.
- [x] Duplicate reading insert protection exists in application logic.
- [x] Supporting duplicate-check index exists on `(meter_id, timestamp, timestamp_source)`.
- [x] Excel and Word report exports are API-key protected when API key mode is enabled.
- [x] SMTP password can be supplied through `SMTP_PASSWORD`.
- [x] UI saves do not store a new plaintext SMTP password while env password is active.
- [x] Backend wait loop is stop-aware between cycles.
- [x] Task Scheduler watchdog startup path exists with rotating lifecycle log.
- [x] PostgreSQL outage readings are buffered in a bounded durable SQLite spool.
- [x] Spool replay is duplicate-safe and isolated per meter.
- [x] Meter clock drift is checked before trusting meter timestamps.
- [x] Scheduled reports/email run in a separate stop-aware worker.
- [x] Daily backup script exists.
- [x] Runtime health check script exists.
- [x] Frontend build is served by backend from `frontend\dist`.

## Remaining Production Conditions

These must be completed before full production signoff:

- [ ] Plant soak test evidence.
- [ ] Watchdog crash/restart test evidence.
- [ ] Database outage spool/replay test evidence.
- [ ] Backup/restore proof.
- [ ] Time-sync discipline.
- [ ] Duplicate-history cleanup.
- [ ] Future DB unique index migration.
- [ ] Optional archive-before-delete for compliance.

## Suggested Soak Test

Minimum for pilot signoff:

- 72 continuous hours with the real plant PC and real connected meters.

Recommended for production signoff:

- 7 continuous days with production-like meter count, backup schedule, report schedule, and normal plant network conditions.

## Soak Test Acceptance Criteria

Accept if:

- backend remains running or restarts automatically after a controlled reboot
- PostgreSQL remains healthy
- expected enabled meters stay online except for known physical interruptions
- latest readings keep advancing
- no unhandled crash loop occurs
- no unexpected database growth spike occurs
- backup task creates usable `.dump` files
- at least one backup is restored into a test database
- Excel and Word exports work
- scheduled email reports work if SMTP is in scope
- logs contain no repeated unresolved database or COM failures
- Windows clock remains correct

Record evidence:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\collect_pilot_evidence.ps1 -Label production-soak
```

## Backup / Restore Proof

Required:

- [ ] daily backup task installed
- [ ] manual backup created
- [ ] backup file listed with `pg_restore -l`
- [ ] latest backup restored into a temporary database
- [ ] row counts checked after restore
- [ ] dashboard/report data verified after restore test

## Time-Sync Discipline

Required:

- [ ] Windows time sync enabled
- [ ] time source documented
- [ ] monthly time check added to operations routine
- [ ] incident process documented for wrong clock

Why it matters:

- readings use timestamps
- retention cleanup uses current time
- scheduled reports use local time

## Duplicate-History Cleanup

Before adding a hard database unique index, inspect existing history:

```sql
SELECT meter_id, timestamp, timestamp_source, COUNT(*) AS duplicate_count
FROM readings
GROUP BY meter_id, timestamp, timestamp_source
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, timestamp DESC;
```

If duplicates exist:

1. Take PostgreSQL backup.
2. Decide which row to keep per duplicate group.
3. Usually keep the lowest `id` or latest `collected_at`.
4. Delete duplicate extras.
5. Re-run duplicate query.

## Future DB Unique Index Migration

After duplicate cleanup:

```sql
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_readings_meter_timestamp_source_unique
ON readings (meter_id, timestamp, timestamp_source);
```

Keep the application-level duplicate check even after adding the unique index. It gives cleaner logs and avoids normal insert errors during duplicate cases.

## Optional Archive-Before-Delete

Current retention deletes old readings after `READINGS_RETENTION_DAYS`.

If compliance or customer requirements need long-term raw history, add an archive process before reducing retention:

- monthly CSV or PostgreSQL dump of old readings
- copy archive to approved storage
- verify archive is readable
- then allow retention cleanup

## Signoff Table

| Area | Owner | Evidence | Status |
| --- | --- | --- | --- |
| Plant soak test | Plant/maintenance | evidence folder, logs, health checks | Pending |
| Backup/restore proof | IT/DB owner | backup file, restore notes | Pending |
| Time sync | IT/maintenance | `w32tm /query /status` output | Pending |
| Duplicate cleanup | Developer/DB owner | duplicate query output | Pending |
| Unique index migration | DB owner | migration result | Pending |
| Report/email validation | Operations | export/email test result | Pending |
