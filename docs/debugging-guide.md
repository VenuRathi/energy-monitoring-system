# Debugging Guide

This guide is for developers diagnosing runtime, deployment, data, and frontend issues.

## First triage order

When something is wrong, check in this order:

1. Is the backend process running?
2. Does `/api/health` respond?
3. Does `/api/status` show polling moving?
4. Is PostgreSQL reachable?
5. Is the COM port present and free?
6. Are the enabled meter definitions correct?
7. Are new rows appearing in `readings`?
8. Is the frontend failing because of missing data or because the backend/API is down?

## Backend won’t start

Check:

- `.venv` exists
- `pip install -r requirements.txt` completed
- `.env` exists
- Python version is the expected one
- PostgreSQL credentials in `.env` are correct

Useful commands:

```powershell
.\.venv\Scripts\python.exe main.py
curl http://127.0.0.1:5000/api/health
```

## `/api/health` fails

Check:

- backend process is running
- `API_HOST` / `API_PORT` are what you think they are
- firewall is not blocking the port

## `/api/status` looks stuck

Check these fields:

- `polling.running`
- `polling.totalCyclesCompleted`
- `polling.lastCycleStartTime`
- `polling.lastCycleEndTime`
- `polling.lastGlobalPollingError`

If `totalCyclesCompleted` is not increasing:

- backend may be hung or not actually running the poll loop
- inspect backend logs immediately

## PostgreSQL down or degraded

Symptoms:

- `/api/health` or `/api/status` shows database degraded
- dashboard/report endpoints may fail clearly

Check:

```powershell
psql -h 127.0.0.1 -U postgres -d energy_monitoring
```

Also verify:

- `.env` DB values
- PostgreSQL service state

## No new readings in the database

Check:

```sql
SELECT meter_id, MAX(collected_at)
FROM readings
GROUP BY meter_id
ORDER BY meter_id;
```

If rows are not updating:

- inspect `/api/status`
- inspect COM port
- inspect meter config
- inspect logs for insert failures or collector failures

## COM port not found

Symptoms:

- startup/runtime warning about missing COM port
- meter polling never succeeds

Check:

- Device Manager → Ports (COM & LPT)
- correct COM number
- adapter cable/driver stability

## COM port locked by another app

Symptoms:

- repeated open/read failures
- port exists but connection never succeeds

Check for:

- QModMaster
- serial terminals
- vendor software
- another instance of this project

## Wrong slave ID

Symptoms:

- polling attempts happen
- no useful readings
- one meter fails while others may continue

Check:

- physical meter address
- configured `slave_id`

## Duplicate slave IDs on same COM port

Current expected behavior:

- backend logs a clear warning
- duplicate meter config is skipped
- other valid meters continue

Fix:

- each enabled meter on the same RS485 bus must have a unique `slave_id`

## Serial settings conflict on same COM port

Current expected behavior:

- backend logs a warning
- conflicting meter is skipped

Fix:

- align `baud_rate`, `parity`, `stop_bits`, `byte_size`, and `timeout`

## Meter stays warning/offline

Check:

- `lastSuccessfulReadingTime`
- `consecutiveFailureCount`
- COM port
- slave ID
- serial settings
- whether the meter is actually powered and wired

## Dashboard empty

Check:

1. `/api/dashboard`
2. `/api/meters`
3. `/api/status`
4. browser console
5. network tab

Important distinction:

- “no readings yet” is a valid empty-state case
- backend/API failure is a different issue entirely

## Frontend build issue

Use:

```powershell
cd frontend
npm run typecheck
npm run build
```

If TypeScript fails:

- check `frontend/src/types/energy.ts`
- check API response shape changes

## Export/report issue

Check:

- chosen meter exists
- start < end
- date range not too large
- rows exist for that time range

Backend side:

- `app/api/service.py`

Frontend side:

- `frontend/src/components/reports/`
- `frontend/src/api/httpClient.ts`

## API key issue

Check:

- `API_KEY_ENABLED`
- `API_KEY`
- `VITE_API_KEY`

Write/control endpoints require:

- `X-API-Key` header

Read-only dashboard endpoints do not.

## Log files to inspect

- `logs/energy_monitoring.log`
- rotated backups in the same directory

Useful patterns:

- `Polling cycle started`
- `Polling cycle ended`
- `Collector read failed`
- `Database insert failed`
- `duplicate slave_id`
- `serial settings conflict`
