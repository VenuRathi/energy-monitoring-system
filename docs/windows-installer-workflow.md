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
- creates app directories like `logs\`, `backups\`, and `release\`
- creates Start Menu entries
- can create a desktop shortcut
- opens the deployment guide after install if desired

## What it does not do yet

It does not:

- install Python automatically
- install PostgreSQL automatically
- create the virtual environment automatically
- install Python dependencies automatically
- fully register Task Scheduler automatically during setup

That is intentional for the current project stage.

## Prerequisites

1. Build the frontend:

```powershell
cd frontend
npm ci
npm run build
cd ..
```

2. Prepare the release bundle:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_release_bundle.ps1
```

3. Install Inno Setup on the machine where you will build the installer.

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

## Recommended target-machine workflow

After running the installer on the target PC:

1. Open the installed folder
2. Copy `.env.example` to `.env`
3. Fill the real environment values
4. Create `.venv`
5. Run `pip install -r requirements.txt`
6. Confirm PostgreSQL and COM port settings
7. Run backend manually once
8. Register the Task Scheduler backend startup

## Why this is still useful

Even without a fully standalone runtime bundle, this gives you:

- a cleaner internal install artifact
- a more professional submission/demo story
- a direct path to future packaging improvements

## Later improvements

Future installer upgrades can add:

- prerequisite checks
- bundled Python strategy
- first-run setup helper
- scheduled-task registration during install
- post-install verification
