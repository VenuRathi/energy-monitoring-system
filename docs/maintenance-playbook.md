# Maintenance Playbook

This playbook is for the developer or engineer responsible for keeping the system healthy after handover.

## Daily checks

Check:

- backend process is running
- `/api/health` responds
- `/api/status` responds
- polling cycle count is increasing
- enabled meters are not unexpectedly stale/offline

## Weekly checks

Check:

- latest readings in PostgreSQL
- database size
- backend log file growth
- scheduled task/service still enabled
- exports still work

## Monthly checks

Check:

- backup files are actually being created
- database growth trend
- meter configuration still matches physical installation
- no duplicate or conflicting meter definitions were introduced

## Logs to inspect

Primary log:

- `logs/energy_monitoring.log`

Look for recurring patterns:

- repeated collector failures
- repeated COM reconnect attempts
- database insert failures
- duplicate slave ID warnings
- serial settings conflict warnings

## Restart procedure

Manual backend restart:

```powershell
cd D:\FFPL\energy-monitoring-system
.\.venv\Scripts\python.exe main.py
```

If Task Scheduler is used:

- restart the scheduled task or stop/start backend task through Task Scheduler

## Frontend rebuild steps

When frontend code changes:

```powershell
cd D:\FFPL\energy-monitoring-system\frontend
npm ci
npm run typecheck
npm run build
```

If backend serves `frontend/dist`, rebuild must be done before operators see the new frontend.

## Database checks

Latest updates:

```sql
SELECT meter_id, MAX(collected_at)
FROM readings
GROUP BY meter_id
ORDER BY meter_id;
```

Row counts:

```sql
SELECT meter_id, COUNT(*) AS reading_count
FROM readings
GROUP BY meter_id
ORDER BY meter_id;
```

Database size:

```sql
SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size;
```

## Backup routine

Use the baseline guidance in:

- [backup-and-maintenance.md](backup-and-maintenance.md)

Minimum expectation:

- daily PostgreSQL backup
- periodic verification that backup files are valid

## If replacing the plant/server PC

Carry over:

- project folder
- `.env`
- PostgreSQL backup/restore
- `config/` customizations if any
- frontend build artifact
- scheduled task/service configuration

Then re-verify:

- Python
- PostgreSQL
- COM port
- meter polling
- `/api/status`

## Restore/replace checklist

1. install Python
2. install PostgreSQL
3. restore project folder
4. recreate `.venv`
5. restore DB backup
6. restore `.env`
7. verify COM port
8. build frontend if needed
9. start backend
10. verify `/api/status`

## When to escalate code changes instead of maintenance

If any of these happen repeatedly:

- meter logic requires new register maps
- exports consistently fail because of code errors
- `/api/status` is logically wrong
- DB growth becomes operationally risky
- operator workflows are too confusing

then this is not just maintenance anymore and should become tracked development work.
