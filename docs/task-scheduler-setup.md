# Task Scheduler Setup

This is the recommended 24/7 Windows run method for the pilot if you do not want to install NSSM immediately.

## Why Task Scheduler is a good pilot choice

- built into Windows
- no extra service wrapper required
- can auto-start after reboot
- can restart after failure
- practical for a pilot plant PC

## Backend runner used

Use:

- [scripts/run_backend_service.bat](../scripts/run_backend_service.bat)

This runner is non-interactive and intended for scheduled-task/service use.

It also:

- creates the `logs/` folder if missing
- starts Python in unbuffered UTF-8 mode
- warns if `.env` is missing before launch

## Register the task automatically

PowerShell as Administrator:

```powershell
cd C:\EnergyMonitoring\energy-monitoring-system
powershell -ExecutionPolicy Bypass -File .\scripts\install_task_scheduler_backend.ps1
```

This registers:

- task name: `EnergyMonitoringBackend`
- triggers: startup and logon
- restart retries enabled

## Register manually in Task Scheduler

If you prefer the GUI:

1. Open Task Scheduler
2. Create Task
3. Name: `EnergyMonitoringBackend`
4. Run whether user is logged on or not
5. Run with highest privileges
6. Trigger:
   - At startup
   - Optional: At log on
7. Action:
   - Program/script: `cmd.exe`
   - Arguments:

```text
/c "C:\EnergyMonitoring\energy-monitoring-system\scripts\run_backend_service.bat"
```

8. Start in:

```text
C:\EnergyMonitoring\energy-monitoring-system
```

9. Settings:
   - restart on failure
   - allow task to be run on demand
   - start when available

## Verify the task

After registration:

1. Run the task manually once
2. Check `logs/energy_monitoring.log`
3. Open:
   - `http://127.0.0.1:5000/api/health`
   - `http://127.0.0.1:5000/api/status`

Recommended log review after first scheduled run:

- startup configuration summary
- detected COM ports
- validated enabled meter summary
- any duplicate `slave_id` or serial settings warnings

## NSSM option

If your team prefers NSSM later, that is also a valid approach.

For this pilot, Task Scheduler is simpler because:

- it is already on Windows
- it is easy for local IT/support to inspect
- it avoids adding another dependency
