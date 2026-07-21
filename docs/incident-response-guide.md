# Incident Response Guide

Use this guide when the production/pilot system is not behaving normally.

Start here for most incidents:

```powershell
cd D:\FFPL\energy-monitoring-system
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1 -MinimumExpectedEnabledMeters 2
```

Check logs:

```text
logs\energy_monitoring.log
logs\backend_runner.log
```

## Meters Stop Updating

Symptoms:

- meter status warning/offline
- latest reading timestamp is old
- `staleWarning=True`
- logs show Modbus read failures

Actions:

1. Check meter power.
2. Check RS485 wiring.
3. Check USB-to-RS485 adapter.
4. Check Device Manager COM port.
5. Confirm COM port did not change after reboot.
6. Confirm no other software is using the COM port.
7. Confirm meter slave ID.
8. Wait one polling cycle.
9. Run health check again.

If only one meter fails, focus on that meter/slave/wiring.

If all meters fail, focus on adapter, COM port, shared serial settings, or backend process.

## Reports Fail

Symptoms:

- Excel/Word export fails
- scheduled email report fails
- browser shows API error

Actions:

1. Confirm backend is reachable.
2. Confirm database status is ok.
3. Confirm selected date range has readings.
4. Confirm start time is before end time.
5. Confirm API key setup if `API_KEY_ENABLED=true`.
6. Check `logs\energy_monitoring.log`.
7. For email reports, check SMTP section below.

Remember: Excel and Word report downloads are API-key protected when API key mode is enabled.

## Database Connection Fails

Symptoms:

- `/api/status` shows database degraded
- logs show database connection errors
- dashboard/report data fails

Actions:

1. Check PostgreSQL service.
2. Check `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=postgres
DB_PASSWORD=...
```

3. Test with `psql`.
4. Check disk free space.
5. Restart PostgreSQL if needed.
6. Restart backend task:

```powershell
Stop-ScheduledTask -TaskName EnergyMonitoringBackend
Start-ScheduledTask -TaskName EnergyMonitoringBackend
```

7. Run health check.

## Frontend Cannot Connect

Symptoms:

- browser cannot open app
- dashboard says backend unavailable
- browser network errors

Actions:

1. Open local app on plant PC:

```text
http://127.0.0.1:5000
```

2. Check API:

```text
http://127.0.0.1:5000/api/health
```

3. Check backend scheduled task.
4. Check firewall port `5000`.
5. If using another PC, open:

```text
http://PLANT_PC_IP:5000
```

6. Confirm `API_HOST=0.0.0.0` for LAN access.
7. Confirm `frontend\dist\index.html` exists.

## API Key / Auth Errors

Symptoms:

- browser shows `Missing API key`
- browser shows `Invalid API key`
- exports or saves fail

Actions:

1. Check `.env`:

```env
API_KEY_ENABLED=true
API_KEY=...
VITE_API_KEY=...
```

2. Confirm `API_KEY` and `VITE_API_KEY` match.
3. Rebuild frontend after changing `VITE_API_KEY`:

```powershell
cd D:\FFPL\energy-monitoring-system\frontend
npm run build
```

4. Restart backend after changing `.env`.
5. Refresh browser.

## SMTP / Email Fails

Symptoms:

- SMTP health says not configured
- test email fails
- scheduled emails fail

Actions:

1. Check `.env` SMTP settings.
2. Prefer `SMTP_PASSWORD` in `.env` or machine environment.
3. Confirm SMTP port:
   - TLS usually `587`
   - SSL usually `465`
4. Confirm firewall allows outbound SMTP.
5. Confirm username/from address are accepted by mail server.
6. Send test email from Reports page.
7. Check backend log for SMTP error.

Important:

- If `SMTP_PASSWORD` exists in environment, it overrides the UI/database password.
- UI saves will not store a new plaintext password while env password is active.

## Power Failure Or Unexpected Restart

Expected recovery:

- Windows restarts.
- PostgreSQL service starts.
- scheduled task `EnergyMonitoringBackend` starts.
- backend resumes polling.

Actions:

1. Confirm Windows time is correct.
2. Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1 -MinimumExpectedEnabledMeters 2
```

3. Check `logs\backend_runner.log` for restart time.
4. Check `logs\energy_monitoring.log` for startup warnings.
5. Confirm COM port did not change.
6. Confirm latest readings resumed.

## Clock / Time-Sync Issue

Symptoms:

- readings appear in future or past
- reports show wrong time windows
- scheduled reports send at wrong time
- retention behavior becomes suspicious

Actions:

1. Check current time:

```powershell
Get-Date
w32tm /query /status
```

2. Correct Windows time sync.
3. Restart backend if timestamps were affected.
4. Check latest readings after correction.
5. Record incident in operations log.

Do not reduce retention settings while time sync is wrong.

## Files To Check First

Use these in order:

1. `logs\energy_monitoring.log`
2. `logs\backend_runner.log`
3. `.env`
4. `config\meter_config.json`
5. `frontend\dist\index.html`
6. Task Scheduler:
   - `EnergyMonitoringBackend`
   - `EnergyMonitoringDailyBackup`
7. Windows Device Manager COM ports
8. PostgreSQL service status
