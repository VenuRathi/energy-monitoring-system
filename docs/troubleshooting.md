# Troubleshooting

This troubleshooting guide is focused on the plant-PC pilot.

## Backend does not start

Check:

- `.venv` exists
- `python main.py` runs manually
- `.env` exists
- PostgreSQL is reachable

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

## `/api/status` shows polling not moving

Check:

- `polling.running`
- `totalCyclesCompleted`
- recent `lastCycleStartTime` / `lastCycleEndTime`
- backend log file

## Meter shows warning/offline

Check:

- COM port exists
- RS485 adapter connected
- no other serial tool is holding the COM port
- correct `slave_id`
- correct serial settings
- meter is enabled only if physically installed

## Duplicate slave ID on same COM port

Current behavior:

- backend logs a clear warning
- bad meter config is skipped safely
- good meters continue

Fix:

- assign unique slave IDs on the RS485 bus

## Serial settings conflict on same COM port

Current behavior:

- backend logs a warning
- conflicting meter is skipped
- other valid meters continue

Fix:

- align baud, parity, stop bits, byte size, and timeout for meters sharing the same bus

## COM port not present

Current behavior:

- startup warning logged
- polling retries continue if the adapter reconnects later

Fix:

- check Device Manager
- reconnect USB-RS485 adapter
- verify COM number did not change

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
