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
- appends runner start/exit events to `logs\backend_runner.log`

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
- default run context: `SYSTEM`
- long execution time limit so the task is not stopped like a short-lived batch job

If you specifically need the task to run as the current user instead, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_task_scheduler_backend.ps1 -RunAsCurrentUser
```

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
2. Check `logs/backend_runner.log`
3. Check `logs/energy_monitoring.log`
4. Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1
```

5. Open:
   - `http://127.0.0.1:5000/api/health`
   - `http://127.0.0.1:5000/api/status`

Recommended log review after first scheduled run:

- runner invocation timestamps in `backend_runner.log`
- startup configuration summary
- detected COM ports
- validated enabled meter summary
- any duplicate `slave_id` or serial settings warnings

## User-login fallback

If Windows blocks Task Scheduler registration because the current user does not have permission, use the current-user Startup folder fallback:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_user_startup_backend.ps1
```

This is weaker than a SYSTEM scheduled task because it starts after user login, not at machine boot. It is still useful for a supervised pilot PC when admin rights are not available.

## NSSM option

If your team prefers NSSM later, that is also a valid approach.

For this pilot, Task Scheduler is simpler because:

- it is already on Windows
- it is easy for local IT/support to inspect
- it avoids adding another dependency
