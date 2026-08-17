# Temporary Plant Energy Monitor Control Utility

This is a temporary, user-level testing convenience tool. It is separate from the Plant Energy Monitor dashboard viewer.

## Separate utilities

- `Plant Energy Monitor Control.lnk` opens the control utility only.
- `Plant Energy Monitor.lnk` opens the dashboard viewer only at `http://127.0.0.1:5000`.
- The dashboard launcher does not start or stop the backend.
- Closing either window does not stop the backend.

## Start System

If the production `EnergyMonitoringBackend` scheduled task is registered, the
Start System button starts that task. If the task is not registered, it launches
the existing `scripts\run_backend_watchdog.vbs` hidden through `wscript.exe`.
When task control requires elevation, the utility requests a normal Windows UAC
Administrator approval; it does not store credentials or open the dashboard.

The watchdog retains its existing global mutex, PID/lock behavior, hidden
`.venv\Scripts\python.exe` launch, health checks, restart handling, and
lifecycle logging. The control utility waits for `/api/status` to become
reachable and does not open a browser.

## Stop System

The Stop System button requests UAC elevation when needed, then invokes the
existing `scripts\stop_backend_task.ps1` procedure. That procedure verifies the
project PID and backend identity, stops the scheduled task if present, stops the
verified watchdog parent when applicable, and stops the verified backend. The
utility then checks that the configured local API port has no listener. It does
not delete data, configuration, PID, lock, or log files itself.

If UAC approval is cancelled or unavailable, the utility reports that the stop
was not completed. Do not use a broad `taskkill /IM python.exe` command.

## Manual commands

From the project root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\plant_energy_monitor_control.ps1 -Action Start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\plant_energy_monitor_control.ps1 -Action Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\plant_energy_monitor_control.ps1 -Action Refresh
```

This tool is not a replacement for Administrator Task Scheduler registration and does not provide boot-level 24/7 operation.
