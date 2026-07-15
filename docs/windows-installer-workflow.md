# Windows Installer Workflow

This is the next-step packaging workflow after the release bundle stage.

It is not a fully standalone installer yet.

It is an installer starter that packages the prepared application bundle into a more software-like Windows install flow.

## What this stage is for

Use this when you want:

- a more professional internal delivery artifact
- an easier handoff to another Windows PC
- a clearer bridge toward a real product install experience

## What it does

The Inno Setup script:

- installs the prepared application folder
- installs it to a writable machine location under `C:\ProgramData\Plant Energy Monitor`
- creates app directories like `logs\`, `backups\`, and `release\`
- creates Start Menu entries
- can create a desktop shortcut
- adds first-run and post-install helper shortcuts
- adds a startup-registration shortcut for Task Scheduler
- opens the deployment guide after install if desired

## What it does not do yet

It does not:

- install Python automatically
- install PostgreSQL automatically
- create the virtual environment automatically
- install Python dependencies automatically
- fully register Task Scheduler automatically during setup

That is intentional for the current project stage.

## Included helpers

After install, the package now includes:

- `scripts\first_run_setup.ps1`
- `scripts\post_install_check.ps1`

What they do:

- create expected local folders
- create `.env` from `.env.example` if missing
- confirm whether frontend build exists
- check whether Python, `pg_dump`, `.venv`, and COM ports are visible
- optionally check whether the backend API is reachable

## Prerequisites

1. Build the frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run build
cd ..
```

2. Prepare the release bundle:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_release_bundle.ps1
```

3. Validate the latest release bundle:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate_release_bundle.ps1 -RequireZip
```

4. Install Inno Setup on the machine where you will build the installer.

## Installer source file

- [installer/energy_monitoring_system.iss](../installer/energy_monitoring_system.iss)

## Compile command

Example:

```powershell
ISCC.exe /DSourceRoot="D:\FFPL\energy-monitoring-system\release\energy-monitoring-system-pilot_YYYY-MM-DD_HHMMSS\energy-monitoring-system" .\installer\energy_monitoring_system.iss
```

Notes:

- `SourceRoot` must point to the prepared application folder inside the release bundle
- the script writes installer output to `installer\output\`

Or use the helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1
```

That script automatically:

- finds the latest prepared release bundle
- validates the bundle first unless you explicitly skip that step
- finds `ISCC.exe`
- compiles the installer against that bundle

## Recommended target-machine workflow

After running the installer on the target PC:

1. Run **First-Run Setup**
2. Edit `.env` with real values
3. Run **Python Environment Bootstrap**
4. If needed, rerun it with `-Recreate`
5. Run **Post-Install Check**
6. Confirm PostgreSQL and COM port settings
7. Launch **Plant Energy Monitor** from the Start Menu
8. Run **Register Backend Startup** so the backend restarts after reboot

## Why this is still useful

Even without a fully standalone runtime bundle, this gives you:

- a cleaner internal install artifact
- a more professional submission/demo story
- a direct path to future packaging improvements

## Later improvements

Future installer upgrades can add:

- prerequisite checks
- bundled Python strategy
- scheduled-task registration during install
- post-install verification
