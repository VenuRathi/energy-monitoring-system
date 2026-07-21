# Pilot Validation Results

This file records the latest real-meter validation performed on the plant PC.

## 2026-07-21 Two-Meter Baseline

Environment:

- Plant/project path: `D:\FFPL\energy-monitoring-system`
- Backend: running from `.venv\Scripts\python.exe main.py`
- API: `http://127.0.0.1:5000`
- Database: PostgreSQL reachable
- COM ports visible: `COM3`, `COM4`, `COM6`
- Active Modbus line: `COM6`
- Poll interval: `18` seconds

Meters validated:

| Meter | COM | Slave ID | Result |
|---|---:|---:|---|
| `MTR-001` | `COM6` | `1` | Online, fresh readings persisted |
| `MTR-002` | `COM6` | `2` | Online, fresh readings persisted |
| `MTR-003` | `COM6` | `3` | Disabled, not part of active pilot polling |

Evidence folders:

- `pilot-evidence\2026-07-21_102247_two-meter-baseline`
- `pilot-evidence\2026-07-21_102340_two-meter-after-export`
- `pilot-evidence\2026-07-21_102610_two-meter-backup-health-ok`

Confirmed:

- Backend started successfully.
- PostgreSQL startup preflight succeeded.
- The API became reachable.
- The frontend production build was detected.
- Two enabled meters were validated for polling startup.
- `MTR-001` and `MTR-002` both responded on `COM6`.
- Readings were persisted for both active meters.
- Strict runtime health check passed with two expected enabled meters.
- Excel export generated: `two-meter-report.xlsx`.
- Word export generated: `two-meter-report.docx`.
- Manual PostgreSQL backup generated successfully.
- User-login startup fallback installed:
  `C:\Users\venur\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\EnergyMonitoringBackend.cmd`

Notes:

- Initial poll logs reported zero/empty primary live measurements, but later health checks marked both enabled meters online and updating.
- This likely means communication is working, while the connected meter/load state may currently have zero live values or unavailable primary values.
- Task Scheduler registration was blocked by Windows permissions. Use the installed user-login fallback for now, or rerun `scripts\install_task_scheduler_backend.ps1` from an Administrator PowerShell window for stronger boot-level startup.

Still pending for full 24/7 proof:

- Cold reboot recovery test.
- COM disconnect/reconnect recovery test.
- PostgreSQL outage/recovery test.
- Overnight soak test.
