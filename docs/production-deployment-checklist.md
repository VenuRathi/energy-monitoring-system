# Production Deployment Checklist

Use this checklist when installing the Energy Monitoring System on a plant PC or local server.

Recommended project root in this deployment:

```text
D:\FFPL\energy-monitoring-system
```

If installed elsewhere, replace this path in all commands.

## 1. Windows Machine / Server Setup

- [ ] Windows PC/server is assigned and approved for 24/7 runtime.
- [ ] Machine has stable power or UPS where possible.
- [ ] Windows automatic sleep/hibernation is disabled.
- [ ] Windows time sync is enabled and working.
- [ ] Local administrator access is available for install and scheduled tasks.
- [ ] Disk has enough free space for PostgreSQL, logs, backups, and `frontend\dist`.
- [ ] Project folder exists:

```powershell
cd D:\FFPL\energy-monitoring-system
```

## 2. PostgreSQL Requirements

- [ ] PostgreSQL 14+ is installed.
- [ ] PostgreSQL service starts automatically with Windows.
- [ ] Database exists:

```sql
CREATE DATABASE energy_monitoring;
```

- [ ] `.env` points to the correct database:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=postgres
DB_PASSWORD=replace_with_real_password
DB_CONNECT_TIMEOUT_SECONDS=5
```

- [ ] PostgreSQL port `5432` is kept local-only unless IT has approved remote DB access.
- [ ] `pg_dump.exe` is available on PATH or in a standard PostgreSQL install folder.

## 3. Python / Backend Setup

- [ ] Python 3.11+ is installed. Python 3.13 has been validated.
- [ ] Virtual environment exists:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_python_env.ps1
```

- [ ] Backend starts manually:

```powershell
.\.venv\Scripts\python.exe main.py
```

- [ ] API health works:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1 -MinimumExpectedEnabledMeters 2
```

## 4. Frontend Build / Setup

- [ ] Node dependencies are installed:

```powershell
cd D:\FFPL\energy-monitoring-system\frontend
npm ci
```

- [ ] Frontend typecheck passes:

```powershell
npm run typecheck
```

- [ ] Frontend production build exists:

```powershell
npm run build
```

- [ ] File exists:

```text
D:\FFPL\energy-monitoring-system\frontend\dist\index.html
```

The backend serves the built frontend from `/`.

## 5. Environment Variables

Create `.env` from `.env.example` and set real values:

```powershell
Copy-Item .env.example .env
```

Minimum production values:

```env
ENABLE_DATABASE=true
DEMO_MODE=false
POLL_INTERVAL_SECONDS=18
APP_TIMEZONE=Asia/Calcutta
METER_CLOCK_MAX_DRIFT_SECONDS=120

API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=false
API_ALLOWED_ORIGINS=http://PLANT_PC_IP:5000
API_KEY_ENABLED=true
API_KEY=replace_with_strong_random_secret

VITE_API_BASE_URL=
VITE_API_KEY=replace_with_same_strong_random_secret

DB_HOST=localhost
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=postgres
DB_PASSWORD=replace_with_real_password
DB_CONNECT_TIMEOUT_SECONDS=5

READINGS_RETENTION_DAYS=1825
READINGS_CLEANUP_BATCH_SIZE=5000
READINGS_CLEANUP_INTERVAL_HOURS=1
READING_SPOOL_PATH=data/reading_spool.sqlite3
READING_SPOOL_MAX_ROWS=100000
READING_SPOOL_MAX_ROWS_PER_METER=50000
READING_SPOOL_RETENTION_DAYS=30
READING_SPOOL_REPLAY_BATCH_SIZE=500
REPORT_WORKER_ENABLED=true
REPORT_WORKER_INTERVAL_SECONDS=15
```

Important:

- `API_DEBUG=false` in production.
- If `API_KEY_ENABLED=true`, `API_KEY` and `VITE_API_KEY` must match.
- Rebuild the frontend after changing `VITE_API_KEY`.
- `VITE_API_KEY` is visible in browser files. It is acceptable for controlled LAN deployment, not internet exposure.

## 6. API Key Setup

Protected actions include:

- meter create/update/delete
- meter discovery/sync
- alert rule changes
- report schedule changes
- email settings/test/send
- Excel and Word report downloads

After enabling API key mode:

```env
API_KEY_ENABLED=true
API_KEY=replace_with_strong_random_secret
VITE_API_KEY=replace_with_same_strong_random_secret
```

Then rebuild:

```powershell
cd D:\FFPL\energy-monitoring-system\frontend
npm run build
```

## 7. SMTP Setup Using `SMTP_PASSWORD`

Recommended production setup:

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=replace_with_real_smtp_password
SMTP_FROM_EMAIL=alerts@example.com
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

Behavior:

- If `SMTP_PASSWORD` is set in `.env` or machine environment, it overrides any database password.
- Saving email settings in the UI will not store a new plaintext password while `SMTP_PASSWORD` is configured.
- If `SMTP_PASSWORD` is removed later, re-enter the SMTP password through the UI or `.env`.

## 8. Startup / Restart Behavior

Register the backend watchdog task:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_task_scheduler_backend.ps1
```

Confirm:

- [ ] task name is `EnergyMonitoringBackend`
- [ ] task triggers at startup
- [ ] run context is `SYSTEM` unless IT approved another account
- [ ] `logs\backend_watchdog.log` exists
- [ ] restart-on-failure is enabled as an outer Task Scheduler fallback
- [ ] backend health is healthy after a controlled reboot

The watchdog starts `.venv\Scripts\python.exe main.py`, records lifecycle
events, and restarts the backend after a crash. Do not combine it with a
second automatic user-login launcher on the same plant PC.

## 9. Database Outage Buffering

- [ ] `data\reading_spool.sqlite3` is on a writable local disk
- [ ] `/api/status` normally reports `readingSpool.queuedCount = 0`
- [ ] a controlled PostgreSQL outage test confirms readings queue and replay
- [ ] spool size limits are appropriate for the plant disk capacity

A non-zero spool queue means the database needs attention even if meter
communication remains online.

## 10. Meter / COM Assumptions

- [ ] Meters are Schneider PM5000 / EM6400-style Modbus RTU meters.
- [ ] USB-to-RS485 adapter is stable and visible in Device Manager.
- [ ] COM port is known, for example `COM6`.
- [ ] All enabled meters on the same RS485 bus use the same serial settings.
- [ ] Each enabled meter has a unique `slave_id`.
- [ ] No other software is holding the COM port.
- [ ] Termination and wiring are checked by plant electrical/maintenance staff.

Current validated pilot pattern on this plant PC:

- `MTR-001`: online, `COM5`, slave `1`
- `MTR-002`: online, `COM7`, slave `2`
- `MTR-003`: disabled/offline until physically connected

## 9. Firewall And Ports

- [ ] Allow inbound TCP `5000` only from approved plant LAN clients.
- [ ] Keep PostgreSQL `5432` local-only unless IT approves remote DB access.
- [ ] Allow outbound SMTP port `587` or `465` if email reports are required.
- [ ] Allow DNS and Windows time sync/NTP.

Default service URLs:

```text
http://127.0.0.1:5000
http://PLANT_PC_IP:5000
```

## 10. Scheduled Startup

Register backend scheduled task as Administrator:

```powershell
cd D:\FFPL\energy-monitoring-system
powershell -ExecutionPolicy Bypass -File .\scripts\install_task_scheduler_backend.ps1
```

Default behavior:

- task name: `EnergyMonitoringBackend`
- run context: `SYSTEM`
- trigger: startup
- restart retries: 3 attempts, 1 minute apart
- multiple instances: ignore new
- execution limit: 3650 days

Install daily backup task:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_daily_backup_task.ps1
```

Default backup task:

- task name: `EnergyMonitoringDailyBackup`
- time: `23:30`
- restart retries: 2 attempts, 5 minutes apart

## 11. Restart Behavior After Power Failure

Expected behavior after power returns:

- Windows boots.
- PostgreSQL service starts.
- `EnergyMonitoringBackend` starts at startup.
- Backend checks `.env`, database, frontend build, COM ports, and meter definitions.
- Backend begins polling enabled valid meters.
- Logs are written to `logs\energy_monitoring.log`.
- Watchdog lifecycle is written to `logs\backend_watchdog.log`.

Verify after restart:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1 -MinimumExpectedEnabledMeters 2 -FailOnDegraded
```

## 12. Final Deployment Gate

Before handover, confirm:

- [ ] `/api/health` returns ok.
- [ ] `/api/status` returns ok.
- [ ] Database status is ok.
- [ ] Polling is running.
- [ ] Expected enabled meters are online.
- [ ] Frontend opens at `http://127.0.0.1:5000`.
- [ ] Reports export with API key enabled.
- [ ] SMTP test email works if email reports are required.
- [ ] Backup script creates a `.dump` file.
- [ ] Scheduled task restarts after reboot.
