# 24/7 Operations SOP

This SOP is for plant engineers, maintenance staff, and support users responsible for daily operation.

## Healthy State

The system is healthy when:

- browser opens `http://127.0.0.1:5000` on the plant PC
- `/api/health` is reachable
- `/api/status` shows `status = ok`
- `databaseStatus = ok`
- `polling.running = True`
- `polling.totalCyclesCompleted` increases over time
- expected enabled meters are `online`
- `staleMeterCount = 0`
- latest reading timestamps are recent
- logs do not show repeated database, COM, or meter errors

Run:

```powershell
cd D:\FFPL\energy-monitoring-system
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1 -MinimumExpectedEnabledMeters 2
```

## Daily Checks

Do these once per shift or once per day:

- [ ] Open dashboard.
- [ ] Confirm expected meters are online.
- [ ] Confirm latest readings are updating.
- [ ] Run runtime health check.
- [ ] Check active alerts.
- [ ] Check `logs\energy_monitoring.log` for repeated errors.
- [ ] Confirm yesterday/today backup exists in `backups\`.
- [ ] Confirm Windows clock is correct.

Useful SQL:

```sql
SELECT DISTINCT ON (meter_id)
    meter_id,
    timestamp,
    collected_at
FROM readings
ORDER BY meter_id, collected_at DESC;
```

## Weekly Checks

Do these weekly:

- [ ] Confirm `EnergyMonitoringBackend` scheduled task exists.
- [ ] Confirm `EnergyMonitoringDailyBackup` scheduled task exists.
- [ ] Review `logs\backend_watchdog.log` for unexpected exits and restarts.
- [ ] Review disk free space.
- [ ] Review PostgreSQL database size.
- [ ] Confirm backups can be listed with `pg_restore -l`.
- [ ] Export one Excel report.
- [ ] Export one Word report.
- [ ] Send SMTP test email if email reports are used.
- [ ] Check Device Manager for stable COM port number.

Database size:

```sql
SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size;
```

Row counts:

```sql
SELECT meter_id, COUNT(*) AS reading_count
FROM readings
GROUP BY meter_id
ORDER BY meter_id;
```

Duplicate history check:

```sql
SELECT meter_id, timestamp, timestamp_source, COUNT(*) AS duplicate_count
FROM readings
GROUP BY meter_id, timestamp, timestamp_source
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, timestamp DESC;
```

## Monthly Checks

Do these monthly:

- [ ] Perform restore test into a temporary PostgreSQL database.
- [ ] Review database growth trend.
- [ ] Review `READINGS_RETENTION_DAYS` is still correct for plant/reporting needs.
- [ ] Copy latest backup to approved external/off-PC storage.
- [ ] Check Windows Update/restart schedule with plant operations.
- [ ] Confirm time sync source and recent sync status.
- [ ] Review meter list and disabled meters.
- [ ] Review API key and SMTP password ownership.

## Log Review

Main log files:

```text
D:\FFPL\energy-monitoring-system\logs\energy_monitoring.log
D:\FFPL\energy-monitoring-system\logs\backend_watchdog.log
```

Look for:

- repeated `Modbus read failed`
- repeated `Database insert failed`
- `Readings retention cleanup failed`
- `Scheduled report processing failed`
- meter status changes
- unexpected backend process exits

Repeated warnings matter more than one-off warnings.

## Disk And Database Growth Review

Check:

- Windows disk free space
- `backups\` size
- `logs\` size
- PostgreSQL database size
- readings row counts

Retention behavior:

- default `READINGS_RETENTION_DAYS=1825`
- cleanup runs after polling/report work
- cleanup removes at most `READINGS_CLEANUP_BATCH_SIZE` rows per run
- cleanup waits `READINGS_CLEANUP_INTERVAL_HOURS` between attempts

Set `READINGS_RETENTION_DAYS=0` only when intentionally disabling automatic cleanup.

## Time Sync / NTP Verification

Time must be correct because:

- readings and reports depend on timestamps
- retention cleanup depends on current system time
- scheduled email reports depend on local time

Check Windows time:

```powershell
w32tm /query /status
Get-Date
```

If time is wrong:

1. Stop report decisions until corrected.
2. Fix Windows time sync.
3. Restart backend if needed.
4. Confirm new readings use correct time.

## Meter Communication Checks

If one meter is warning/offline:

- check meter power
- check RS485 wiring
- check slave ID
- check COM port
- check serial settings
- confirm no other tool is holding the COM port
- wait one polling cycle and recheck

If all meters are offline:

- check USB-to-RS485 adapter
- check COM port changed after reboot
- check backend logs
- check Windows Device Manager

## Report Export Checks

Weekly:

- export Excel for one meter and one recent time range
- export Word for same time range
- confirm row count is believable
- if API key mode is enabled, confirm report export works from the browser

If exports fail:

- check selected meter and date range
- check API key setup
- check backend log
- check database connection

## What To Record

Keep a simple operation log:

- date/time
- health status
- meters online/offline
- backup present
- any incident and action taken
- any PC restart
- any COM port change
