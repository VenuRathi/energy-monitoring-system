# Pilot Evidence Log

Use this file to record real plant-PC validation results. Keep screenshots, exports, and API snapshots in a matching evidence folder.

Recommended evidence command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\collect_pilot_evidence.ps1 -Label baseline
```

Run it before and after each important validation test.

## Evidence Folder Convention

Use:

```text
pilot-evidence\YYYY-MM-DD_HHMMSS_test-label\
```

Each folder should contain:

- `summary.txt`
- `api-health.json`
- `api-status.json`
- `environment.txt`
- dashboard screenshot if available
- exported Excel or Word sample if the test includes reports

## Validation Record Template

Copy this block for every field test.

```text
Test name:
Date/time:
Plant PC:
COM adapter:
Meters involved:
Expected result:
Actual result:
Pass/fail:
Evidence folder:
Notes:
```

## Required Pilot Proofs

| Test | Evidence needed | Status |
|---|---|---|
| Baseline healthy state | Dashboard screenshot, `summary.txt`, `/api/status` JSON | Pending field run |
| Cold reboot recovery | Before/after evidence folders, cycle count moving after reboot | Pending field run |
| COM disconnect/reconnect | Before/disconnected/reconnected evidence folders | Pending field run |
| One bad meter among good meters | Good meter still updating, bad meter warning/offline | Pending field run |
| PostgreSQL outage recovery | Degraded DB status, recovery after DB restart | Pending field run |
| Export sanity | Excel/Word sample from real data range | Pending field run |
| Overnight soak | Start/end evidence folders, log review notes | Pending field run |

## Final Go/No-Go Summary

Fill this after the pilot validation run.

```text
Pilot date:
Run duration:
Enabled live meters:
Polling interval:
Total cycles observed:
Unexpected backend restarts:
Unexpected database failures:
Meters with repeated communication failure:
Export/report result:
Backup result:
Overall decision:
Owner/sign-off:
```
