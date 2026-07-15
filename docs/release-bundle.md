# Release Bundle Workflow

This is the practical step between "run from the repo" and "full Windows installer."

Use it when you want to hand the project to:

- a plant PC
- internal IT/support
- another developer
- your manager for a controlled demo package

## What this does

The release bundle script creates:

- a clean application folder copy
- the built frontend from `frontend/dist`
- the root launcher `run_app.bat`
- deployment docs
- scripts
- a top-level `START_HERE.txt`
- a `.zip` archive for transfer

It does not include:

- a Python virtual environment
- PostgreSQL itself
- real secrets from `.env`

That is intentional.

## Prerequisites

Before creating a bundle:

1. Build the frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run build
cd ..
```

2. Make sure the repo contains the latest scripts/docs you want to ship.

## Create the bundle

From the project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_release_bundle.ps1
```

Default output:

- folder: `release\energy-monitoring-system-pilot_YYYY-MM-DD_HHMMSS\`
- zip: `release\energy-monitoring-system-pilot_YYYY-MM-DD_HHMMSS.zip`

## Validate the bundle

After creating it, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate_release_bundle.ps1 -RequireZip
```

This verifies that the latest bundle still contains the expected:

- backend entry files
- launcher
- frontend build
- setup scripts
- deployment docs
- top-level `START_HERE.txt`
- matching `.zip` archive

## What goes into the bundle

- `main.py`
- `run_app.bat`
- `requirements.txt`
- `README.md`
- `LICENSE`
- `.env.example`
- `app/`
- `config/`
- `docs/`
- `scripts/`
- `utils/`
- `frontend/dist/`

## Recommended use

Use this when:

- copying the project to a plant PC without cloning git
- handing a controlled snapshot to someone else
- freezing a demo-ready delivery

## What to do on the target machine

1. Extract the zip
2. Read `START_HERE.txt`
3. Run `powershell -ExecutionPolicy Bypass -File .\scripts\first_run_setup.ps1`
4. Follow [plant-pc-deployment.md](plant-pc-deployment.md)
5. Run `powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_python_env.ps1`
6. Verify PostgreSQL and COM port setup
7. Run `powershell -ExecutionPolicy Bypass -File .\scripts\post_install_check.ps1`
8. Launch the app with `run_app.bat` or run the backend manually once
9. Register Task Scheduler startup

## Why this exists even before an installer

This gives you:

- a repeatable handoff artifact
- a cleaner deployment snapshot
- a bridge toward a future Inno Setup installer

It is the simplest professional step before full installer packaging.
