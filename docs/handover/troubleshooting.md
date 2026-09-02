# Troubleshooting

This troubleshooting guide is focused on the plant-PC pilot.

## Backend does not start

Check:

- `.venv` exists
- one-time `.\.venv\Scripts\python.exe main.py` smoke works when the scheduled task is stopped
- `.env` exists
- PostgreSQL is reachable
- `logs/backend_watchdog.log` for startup, crash, and restart events

## `/api/health` fails

Check:

- backend process is running
- API port is correct
- Windows firewall allows the required inbound port

## `/api/status` shows database degraded

Check:

- PostgreSQL service is running
- `.env` DB settings are correct
- `psql` can connect locally
- `checks.schemaStartup.message` for the exact schema/startup failure
- `schemaStartup.lastErrorMessage` for the original startup error

## `/api/status` shows polling not moving

Check:

- `polling.running`
- `totalCyclesCompleted`
- recent `lastCycleStartTime` / `lastCycleEndTime`
- backend log file
- whether the Task Scheduler task is still running/enabled on the plant PC

## Meter shows warning/offline

Check:

- `/api/status` `diagnosticCode` / `diagnosticMessage`
- COM port exists
- RS485 adapter connected
- no other serial tool is holding the COM port
- correct `slave_id`
- correct serial settings
- meter is enabled only if physically installed

## Duplicate slave ID on same COM port

Current behavior:

- backend logs a clear warning
- `/api/status` shows `diagnosticCode=duplicate_slave_id`
- bad meter config is skipped safely
- good meters continue

Fix:

- assign unique slave IDs on the RS485 bus
- update the meter in Meter Setup
- wait one polling cycle and recheck `/api/status`

## Serial settings conflict on same COM port

Current behavior:

- backend logs a warning
- `/api/status` shows `diagnosticCode=serial_settings_conflict`
- conflicting meter is skipped
- other valid meters continue

Fix:

- align baud, parity, stop bits, byte size, and timeout for meters sharing the same bus
- use a separate COM port if the device is on a different RS485 bus
- wait one polling cycle and recheck `/api/status`

## COM port missing / changed after reboot

Current behavior:

- startup/runtime warning logged
- `/api/status` shows `diagnosticCode=com_port_missing`
- polling retries continue if the adapter reconnects later
- the meter is not disabled automatically

Fix:

- check Device Manager
- reconnect USB-RS485 adapter
- verify COM number did not change
- if Windows assigned a new COM number, update the meter COM port in Meter Setup
- confirm no enabled meter still shows `COM port missing`

Recovery checklist:

1. Open Device Manager.
2. Expand `Ports (COM & LPT)`.
3. Note the current USB/RS485 adapter COM number.
4. Open Meter Setup.
5. Update each affected enabled meter to the current COM port.
6. Confirm slave IDs and serial settings still match the RS485 bus.
7. Wait one polling cycle.
8. Run `powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1`.

## Meter no response

Current behavior:

- `/api/status` shows `diagnosticCode=meter_no_response`
- other meters continue polling
- retries continue

Fix:

- check meter power
- check RS485 A/B wiring and termination
- verify configured `slave_id`
- verify baud, parity, stop bits, byte size, and timeout
- confirm the meter is physically installed before leaving it enabled

## Dashboard not reachable from another machine

Check:

- `API_HOST=0.0.0.0`
- backend running
- plant PC firewall allows the chosen port
- users are opening the correct plant PC IP

## Frontend does not load in pilot mode

Check:

- `frontend/dist` exists
- `npm run build` was completed
- backend is serving `/`

## Exports fail

Check:

- selected date range is valid
- data exists in the selected period
- backend logs for report generation errors

## No new readings in database

Check:

- `/api/status` meter health
- PostgreSQL is writable
- meter really responded
- meter is enabled

Use:

```sql
SELECT meter_id, MAX(collected_at)
FROM readings
GROUP BY meter_id
ORDER BY meter_id;
```

## Fast runtime summary command

Use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1
```

This gives a quick operator/support summary of:

- API state
- database state
- polling heartbeat
- per-meter status

## Task Scheduler starts but backend is not staying up

Check:

- `logs/backend_watchdog.log`
- `logs/energy_monitoring.log`
- whether `.env` still exists in the installed/project folder
- whether `.venv` is intact
- whether PostgreSQL starts before the backend

If needed:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_task_scheduler_backend.ps1
```

This safely re-registers the scheduled task with the current settings.

For a controlled restart, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_backend_task.ps1
Start-ScheduledTask -TaskName EnergyMonitoringBackend
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1
```
