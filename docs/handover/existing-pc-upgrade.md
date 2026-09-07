# Existing PC Upgrade Runbook

Use this runbook to upgrade an existing Git checkout of Plant Energy Monitor.
It is deliberately different from a fresh installer setup: it preserves the
machine's settings, readings, logs, backups, and scheduled-task configuration.

## Release gate

Only begin after the release owner has recorded an approved commit and the
target PC is in a maintenance window. For the report consistency release, the
release version is `0.2.2`; the precise approved commit is recorded in the
release bundle's `RELEASE_INFO.txt` and `version.json`.

Do not use this procedure for an installer or release-bundle installation that
does not contain `.git`. Use the installer/bundle documentation for that
deployment type instead.

## Before changing files

1. Open PowerShell in the actual application root and identify the current
   state:

   ```powershell
   git status --short
   git rev-parse --short HEAD
   git fetch origin
   git rev-parse --short origin/main
   ```

2. Stop if `git status --short` shows changes outside known, machine-specific
   startup scripts. Do not use `git reset --hard` or overwrite local files.
   Preserve and review those changes first.
3. Capture the current commit as `OLD_SHA` and collect an inventory:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\collect_pc_inventory.ps1
   ```

4. Take a normal PostgreSQL backup using the existing backup procedure. This
   report release has no database migration, so a database restore is not part
   of a normal code rollback; the backup is disaster-recovery protection.
5. Preserve `.env`, `config\meter_config.json`, `data\`, `logs\`, `backups\`,
   `deployment-reports\`, and any local operational patch. Never copy a
   development `.env` or meter configuration onto a production PC.

## Update the checkout

Replace `APPROVED_SHA` with the release owner’s exact approved commit. Pinning
the merge prevents a moving `main` branch from changing the code during the
maintenance window.

```powershell
git fetch origin
git show --no-patch --format=%H APPROVED_SHA
git merge --ff-only APPROVED_SHA
git rev-parse --short HEAD
```

The final SHA must equal `APPROVED_SHA`. If it does not, stop before restarting
the backend.

Build the frontend only when the upgraded commit contains frontend changes:

```powershell
Push-Location frontend
npm ci
npm run build
Pop-Location
```

Do not reinstall Python dependencies unless `requirements.txt` changed. The
`0.2.2` report release does not add a dependency.

## Controlled restart and validation

Use the project stop script; raw Task Scheduler stopping can leave `python
main.py` running and serve stale code.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_backend_task.ps1
Start-ScheduledTask -TaskName EnergyMonitoringBackend
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1
```

Confirm `git rev-parse --short HEAD` in the same root, then validate the
Reports page with real local readings:

- Generate a one-meter Excel report and confirm native charts plus `Graph Data`.
- Generate a multi-meter, interval-based Excel report and confirm charts,
  usage columns, ordered timestamps, and valid zero readings where present.
- Generate a Word report and confirm it opens normally.
- Inspect the next scheduled report after it runs; do not create an extra
  schedule or send a test recipient email without approval.

Record the output directory from `collect_pilot_evidence.ps1` or the validation
tool alongside the deployed SHA.

## Rollback

Roll back for a failed health check, polling failure, report corruption, wrong
date/time window, or unexpected email behavior. Preserve logs and generated
evidence before changing code.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_backend_task.ps1
git switch --detach OLD_SHA
Start-ScheduledTask -TaskName EnergyMonitoringBackend
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1
```

Do not restore an older database backup merely to roll back this report-only
release: that would discard new meter readings. After rollback, document the
detached HEAD state and arrange a reviewed follow-up upgrade.

## OSP-specific protection

OSP currently has known local changes in
`scripts\install_task_scheduler_backend.ps1`,
`scripts\run_backend_watchdog.vbs`, and an operational patch file. Those files
must be preserved and reviewed before any Git update. Do not commit or push
them to the shared branch as part of this report release.
