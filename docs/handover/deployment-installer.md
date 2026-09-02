# Deployment Installer Toolkit

This toolkit is a Windows-first wrapper around the deployment checks used for
plant-PC setup and repair. It is intentionally safe to run multiple times.

Run it from the project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1
```

Useful direct modes:

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode HealthCheck
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode Evidence
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode MeterSetup
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode StartupFallback
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode AdminTask
```

## Modes

`HealthCheck` creates a timestamped report in `deployment-reports/` with COM
ports, meter configuration checks, sanitized `.env`, PostgreSQL service and
connection checks, API status if reachable, and recent log tails.

`Evidence` currently runs the same safe capture as `HealthCheck`. It succeeds
even when the backend API is down, so a failed deployment still produces useful
context.

`MeterSetup` checks enabled meters against detected Windows COM ports. It flags
missing configured ports, duplicate slave IDs on the same COM port, and serial
setting conflicts. It does not guess or modify physical meter mapping.

`StartupFallback` installs the current-user startup launcher. This does not need
Administrator rights, but the backend starts only when that Windows user logs in.

`AdminTask` registers the proper Windows scheduled task. This requires
Administrator PowerShell and is the preferred 24/7 plant-PC setup.

## Admin Boundary

Administrator rights are needed for:

- registering the backend scheduled task as `SYSTEM`
- inspecting scheduled tasks when Windows denies normal-user access
- creating firewall rules for network dashboard access
- changing protected PostgreSQL service settings
- installing blocked USB-RS485 drivers

Administrator rights are not needed for:

- collecting deployment evidence
- checking `.env`, COM ports, and meter config
- installing the current-user startup fallback
- running the backend manually

## Report Files

Each run writes a folder like:

```text
deployment-reports/2026-08-02_153000_health_check/
```

Important files:

- `summary.txt`
- `sanitized-env.txt`
- `meter-config.json`
- `com-ports.txt`
- `postgres-check.txt`
- `api-health.json` or `api-health.txt`
- `api-status.json` or `api-status.txt`
- `logs-tail.txt`

Paste `summary.txt` into Codex when asking for deployment support.
