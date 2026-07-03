# Operations Runbook

This runbook is for day-to-day starting, checking, and troubleshooting the current system.

## Start backend

```powershell
cd D:\FFPL\energy-monitoring-system
.\.venv\Scripts\python.exe main.py
```

Alternative:

```powershell
run_app.bat
```

## Start frontend

```powershell
cd D:\FFPL\energy-monitoring-system\frontend
npm run dev
```

## Verify API health

```powershell
curl http://127.0.0.1:5000/api/health
```

Expected:

- API reachable
- database check ok or skipped depending on mode

## Verify runtime status

```powershell
curl http://127.0.0.1:5000/api/status
```

Look for:

- `status`
- `summary.meters`
- `summary.staleMeterCount`
- `polling.running`
- `polling.lastCycleStartTime`
- `polling.lastCycleEndTime`
- `polling.totalCyclesCompleted`

Healthy live example:

- `MTR-001` online
- `MTR-002` online
- `MTR-003` disabled/offline and not counted stale
- `staleMeterCount = 0`

## Check latest readings in PostgreSQL

Open `psql`:

```powershell
psql -h localhost -U postgres -d energy_monitoring
```

Then run:

```sql
SELECT meter_id, timestamp, collected_at
FROM readings
ORDER BY collected_at DESC
LIMIT 20;
```

## How to know if a meter is online/offline

Use `/api/status`.

Practical meaning:

- `communicationStatus=online`: recent successful polling
- `communicationStatus=warning`: communication issues or partial failures
- `communicationStatus=offline`: repeated failure or stale/no recent success
- `staleWarning=false`: recent success within threshold

## If COM port fails

Symptoms:

- meter goes warning/offline
- logs mention COM open/read failure

Actions:

1. Check Device Manager for the correct COM port
2. Confirm no other tool is holding the port
3. Reconnect the USB/RS485 adapter
4. Wait for the next polling cycle
5. Recheck `/api/status`

## If PostgreSQL is down

Symptoms:

- `/api/health` or `/api/status` shows database degraded
- dashboard/report endpoints may fail clearly instead of showing fake empty data

Actions:

1. Start the PostgreSQL service
2. Confirm `.env` DB settings are correct
3. Test connection with `psql`
4. Restart backend if needed

## If the dashboard shows no readings

Check:

1. `GET /api/status`
2. meter enabled state
3. meter `communicationStatus`
4. latest reading timestamps in PostgreSQL

If the meter is new and has not been polled yet, the UI should show the no-readings state.

## If the dashboard is blank

Check:

1. browser console
2. `GET /api/health`
3. `GET /api/dashboard`
4. CORS/API URL settings
5. whether the backend is actually running

The frontend should now show a useful error instead of a white-screen crash, but backend/API failures can still block data loading.

## If a meter shows stale/offline

Check:

1. physical power to the meter
2. RS485 wiring
3. correct `slave_id`
4. correct COM port
5. serial settings match the meter
6. no other app is holding the COM port
7. `/api/status` timestamps and failure count

## If exports fail

Check:

1. selected meter exists
2. selected date range is valid
3. start is before end
4. range is not too large
5. rows are available in the selected time window
6. backend console for JSON error details

## Log locations

- backend logs: `logs/`
- PowerShell console output during local run

If running a boss demo, keep one terminal visible for backend status and errors.
