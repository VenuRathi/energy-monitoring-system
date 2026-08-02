# Deployment Toolkit

Use this toolkit on the Windows plant PC after Python, Node.js/npm, and PostgreSQL have already been installed manually.

## Start Menu

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1
```

Menu options:

- `Full Setup`: first deployment on a plant PC.
- `Repair Setup`: re-check and repair missing pieces without duplicating working pieces.
- `Database Only`: repair or verify PostgreSQL database/schema/meter rows.
- `Meter/COM Setup Only`: inspect COM ports, meter config, slave IDs, and optionally update meter COM ports.
- In interactive mode, Meter/COM Setup backs up `config/meter_config.json`, then lets the operator choose the detected COM port and slave ID for each enabled meter.
- `Health Check Only`: read-only check of the current PC state.
- `Collect Evidence`: read-only evidence bundle for debugging.

## Non-Interactive Examples

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode Full -NonInteractive
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode Repair -NonInteractive
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode Database -CreateDatabaseIfMissing -NonInteractive
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode MeterSetup -NonInteractive
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode HealthCheck -NonInteractive
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode Evidence -NonInteractive
```

Useful flags:

- `-SkipDatabase`: skip PostgreSQL checks/setup.
- `-SkipFrontendBuild`: verify frontend only; do not run `npm run build`.
- `-SkipMeterTrial`: skip direct Modbus trial reads.
- `-RunAsCurrentUser`: register the backend scheduled task as the current user instead of `SYSTEM`.
- `-ApiBaseUrl http://127.0.0.1:5000`: override the API URL used for smoke checks.

## What Full Setup Does

Full Setup:

- verifies Python, Node.js/npm, and PostgreSQL presence
- creates `.env` from `.env.example` if missing
- ensures project folders exist
- creates or repairs `.venv`
- installs Python dependencies
- creates the configured PostgreSQL database if missing
- applies the app schema idempotently
- upserts configured meters into PostgreSQL
- runs `npm ci` when `frontend/node_modules` is missing
- runs the frontend production build unless skipped
- checks COM ports and meter config safety
- optionally guides COM port updates in interactive mode
- runs direct Modbus trials unless skipped
- registers or updates the `EnergyMonitoringBackend` scheduled task
- writes a deployment report

## Report Files

Each run creates:

```text
deployment/reports/<timestamp>_<mode>/
```

Paste `summary.txt` into a Codex task when asking for help. For deeper debugging, attach or inspect:

- `checks.json`
- `postgres-check.json`
- `meter-trial.json`
- `api-health.json`
- `api-status.json`
- `scheduled-tasks.txt`
- `logs-tail.txt`

## Interpreting Common Results

Examples:

- `PASS: PostgreSQL service is running`: Windows reports PostgreSQL running.
- `FAIL: database connection`: `.env` credentials or PostgreSQL availability are wrong.
- `FAIL: MTR-002 COM port`: meter config references a COM port Windows does not detect.
- `FAIL: MTR-002 slave ID`: duplicate slave ID exists on the same COM port.
- `WARN: API health`: backend is not running or not reachable.
- `WARN: frontend/dist/index.html`: frontend has not been built.

## Safety Notes

The toolkit never drops databases or deletes readings. It does not install Python, Node.js, or PostgreSQL. It does not overwrite `.env`. It backs up `config/meter_config.json` before guided edits.
