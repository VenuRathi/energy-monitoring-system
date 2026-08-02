# Deployment Toolkit Design

## Purpose

The deployment toolkit is a Windows-first recovery and setup layer for plant PCs running the energy monitoring system. It is deliberately a toolkit rather than a one-time installer because plant PCs often need repeated diagnosis after COM port changes, PostgreSQL credential drift, missing frontend builds, scheduled task issues, or meter communication failures.

## Entry Point

The main entry point is:

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1
```

It provides these modes:

- Full Setup
- Repair Setup
- Database Only
- Meter/COM Setup Only
- Health Check Only
- Collect Evidence

The same modes are available non-interactively:

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode Full
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode HealthCheck
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode Evidence
powershell -ExecutionPolicy Bypass -File .\deployment\install.ps1 -Mode MeterSetup
```

## Idempotency Rules

- `.env` is created from `.env.example` only when missing.
- Existing `.env` is not overwritten.
- Meter config changes happen only through the guided wizard and only after a timestamped backup.
- Database schema setup reuses `app.database.models.create_tables`, which is written with `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION`, and idempotent indexes/views.
- Meter rows are upserted into PostgreSQL using the existing `MeterRepository` conflict behavior.
- The backend scheduled task is registered with the existing `install_task_scheduler_backend.ps1`, which uses `Register-ScheduledTask -Force` for a single stable task name.
- Health Check and Evidence modes are read-only.

## Components

- `deployment/install.ps1`: user-facing menu and orchestration script.
- `deployment/lib/DeploymentToolkit.ps1`: reusable PowerShell checks, report writing, frontend checks, scheduled task checks, COM/meter validation, API checks, and artifact collection.
- `deployment/db_setup.py`: Python helper that applies or verifies the database using the app's own settings, meter loader, schema creation, and repositories.
- `deployment/meter_trial.py`: Python helper that performs direct Modbus trial reads without requiring the backend to be running.

## Report Contract

Every run writes a timestamped folder under `deployment/reports/`, for example:

```text
deployment/reports/2026-08-02_153000_full/
```

Important files:

- `summary.txt`
- `checks.json`
- `sanitized-env.txt`
- `meter-config.json`
- `com-ports.txt`
- `postgres-check.txt`
- `postgres-check.json`
- `api-health.json`
- `api-status.json`
- `scheduled-tasks.txt`
- `logs-tail.txt`
- `meter-trial.json` when direct trial runs

Evidence mode also creates a zip next to the report folder.

## Safety Boundaries

The toolkit does not install PostgreSQL, Node.js, or Python. It checks for them and reports clear failures when they are missing.

The toolkit does not drop databases, delete readings, delete logs, or overwrite operator configuration without backup. Database creation is allowed only in Full/Repair mode by default, or in Database mode after explicit operator approval or `-CreateDatabaseIfMissing`.

## Remaining Plant-PC Validation

Direct Modbus trials need the actual USB-RS485 adapter and meters connected. Scheduled task registration may need Administrator privileges depending on the plant PC policy and whether the task runs as `SYSTEM`.
