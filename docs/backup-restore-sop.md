# Backup And Restore SOP

This SOP explains how to back up and restore the PostgreSQL database for the Energy Monitoring System.

## Backup Scope

Back up:

- PostgreSQL database `energy_monitoring`
- `.env`
- `config\meter_config.json`
- `docs\`
- release bundle or installer used for deployment

Do not store real credentials in shared locations unless approved by IT.

## Backup Location Guidance

Default local backup folder:

```text
D:\FFPL\energy-monitoring-system\backups
```

Recommended storage:

- local `backups\` for quick recovery
- copied weekly to a separate drive/server
- protected from ordinary users
- not stored only on the same failing plant PC

## Manual PostgreSQL Backup

Run:

```powershell
cd D:\FFPL\energy-monitoring-system
powershell -ExecutionPolicy Bypass -File .\scripts\backup_postgres.ps1
```

Optional backup folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup_postgres.ps1 -BackupRoot "E:\EnergyMonitoringBackups"
```

Optional retention:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup_postgres.ps1 -RetentionDays 30
```

The script creates a custom-format PostgreSQL dump:

```text
backups\energy_monitoring_yyyy-MM-dd_HHmmss.dump
```

## Scheduled Backup

Install daily backup task as Administrator:

```powershell
cd D:\FFPL\energy-monitoring-system
powershell -ExecutionPolicy Bypass -File .\scripts\install_daily_backup_task.ps1
```

Default:

- task name: `EnergyMonitoringDailyBackup`
- daily time: `23:30`
- runs `scripts\backup_postgres.ps1`

Change time:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_daily_backup_task.ps1 -RunTime "22:00"
```

## Backup Verification

After each backup:

- [ ] `.dump` file exists.
- [ ] file size is greater than 0.
- [ ] timestamp matches backup time.
- [ ] backup can be listed by `pg_restore`.

Example:

```powershell
pg_restore -l .\backups\energy_monitoring_yyyy-MM-dd_HHmmss.dump
```

If `pg_restore` is not on PATH, use the full PostgreSQL bin path.

Monthly verification:

1. Create temporary database.
2. Restore latest backup into temporary database.
3. Check row counts and latest readings.
4. Drop temporary database after verification.

## Restore Procedure On Same PC

Use when PostgreSQL is available but the database needs to be restored.

1. Stop backend task:

```powershell
Stop-ScheduledTask -TaskName EnergyMonitoringBackend
```

2. Confirm no backend Python process is running.

3. Open `psql` as an admin PostgreSQL user.

4. Recreate database if needed:

```sql
DROP DATABASE IF EXISTS energy_monitoring;
CREATE DATABASE energy_monitoring;
```

5. Restore:

```powershell
pg_restore -h localhost -p 5432 -U postgres -d energy_monitoring -c ".\backups\energy_monitoring_yyyy-MM-dd_HHmmss.dump"
```

6. Start backend:

```powershell
Start-ScheduledTask -TaskName EnergyMonitoringBackend
```

7. Verify:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1 -MinimumExpectedEnabledMeters 2
```

## Recovery After PC / Server Replacement

1. Install Windows prerequisites.
2. Install PostgreSQL.
3. Copy project folder or install release bundle.
4. Restore `.env`.
5. Restore `config\meter_config.json` if changed from release.
6. Restore PostgreSQL backup.
7. Build frontend if needed:

```powershell
cd D:\FFPL\energy-monitoring-system\frontend
npm ci
npm run build
cd ..
```

8. Register backend scheduled task:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_task_scheduler_backend.ps1
```

9. Register daily backup task:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_daily_backup_task.ps1
```

10. Confirm COM port and meter slave IDs.

11. Run health check:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1 -MinimumExpectedEnabledMeters 2 -FailOnDegraded
```

## Backup Failure Actions

If backup fails:

- check PostgreSQL service is running
- check `.env` DB credentials
- check `pg_dump.exe` is available
- check disk free space
- run backup manually and capture error
- do not delete old backups until a new good backup exists

## Restore Acceptance Criteria

Restore is successful when:

- backend starts
- `/api/status` database is ok
- latest readings can be queried
- dashboard opens
- meter polling resumes
- reports can export from restored data
