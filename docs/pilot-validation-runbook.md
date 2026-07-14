# Pilot Validation Runbook

This runbook is for the on-site validation phase after deployment.

Use it to prove that the pilot is not only running, but recoverable and understandable under realistic failures.

## Before starting

Confirm:

- backend is already running
- frontend is reachable
- PostgreSQL is up
- at least one good real meter is online

Helpful command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1
```

## Validation 1: Baseline healthy state

Goal:

- confirm the system is healthy before fault testing

Check:

- `/api/health` returns ok
- `/api/status` returns ok
- polling cycle count is increasing
- at least the known good meters are online
- `staleMeterCount = 0` for the expected healthy setup

Record:

- timestamp
- screenshot of dashboard
- output of `check_runtime_health.ps1`

## Validation 2: Cold reboot recovery

Goal:

- confirm the backend restarts after reboot and resumes polling

Steps:

1. Record current cycle count and latest reading time
2. Reboot the plant PC
3. Wait for Windows login/startup completion
4. Confirm Task Scheduler started the backend
5. Open `/api/status`
6. Confirm cycle count starts moving again
7. Confirm new readings appear in PostgreSQL

Pass criteria:

- backend auto-starts without manual intervention
- `/api/status` becomes reachable
- polling resumes
- meters return online

## Validation 3: COM disconnect and reconnect

Goal:

- confirm COM failure does not permanently wedge polling

Steps:

1. Confirm a good meter is online
2. Disconnect the USB-RS485 adapter
3. Wait at least one polling cycle
4. Check `/api/status`
5. Reconnect the adapter
6. Wait another cycle or two
7. Check `/api/status` again

Pass criteria:

- meter goes warning/offline when disconnected
- backend stays running
- polling loop keeps moving
- meter returns online after reconnect

## Validation 4: One bad meter among good meters

Goal:

- prove one wrong meter does not break the rest

Ways to test:

- enable one meter with a wrong `slave_id`
- or temporarily use one disconnected enabled meter

Steps:

1. Keep one known good meter enabled
2. Add or enable one bad meter definition
3. Wait for a few cycles
4. Check `/api/status`
5. Confirm the good meter still updates

Pass criteria:

- bad meter shows warning/offline
- good meter stays online
- polling loop continues

## Validation 5: PostgreSQL outage recovery

Goal:

- prove database failure does not silently fake healthy data

Steps:

1. Confirm healthy baseline first
2. Stop PostgreSQL service
3. Check `/api/health` and `/api/status`
4. Wait one or two cycles
5. Restart PostgreSQL service
6. Check whether normal operation resumes

Pass criteria:

- API clearly reports database degraded
- backend does not crash immediately just because DB failed
- readings resume after PostgreSQL comes back

## Validation 6: Report/export sanity

Goal:

- confirm operator-visible output still works on live data

Steps:

1. Open Reports page
2. Select one known-good meter
3. Choose a recent time range with data
4. Export Excel
5. Generate Word report

Pass criteria:

- files generate successfully
- empty/invalid range errors are clear when intentionally tested

## Evidence to keep

For a strong internship/final submission, keep:

- screenshots of dashboard healthy state
- screenshot of `/api/status`
- one screenshot during fault condition
- one screenshot after recovery
- exported Excel/Word samples
- short notes for each validation result

## Suggested result log format

For each test, note:

- test name
- date/time
- setup used
- expected result
- actual result
- pass/fail
- observations

## If a validation fails

Do not guess.

Capture:

- current `/api/status`
- backend log lines
- exact meter involved
- exact COM/slave setting involved
- what changed immediately before the failure

Then treat that as the next engineering fix item.
