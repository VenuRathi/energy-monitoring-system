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

## What goes into the bundle

- `main.py`
- `requirements.txt`
- `README.md`
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
3. Follow [plant-pc-deployment.md](plant-pc-deployment.md)
4. Create `.env` from `.env.example`
5. Install Python dependencies
6. Verify PostgreSQL and COM port setup
7. Run the backend manually once
8. Register Task Scheduler startup

## Why this exists even before an installer

This gives you:

- a repeatable handoff artifact
- a cleaner deployment snapshot
- a bridge toward a future Inno Setup installer

It is the simplest professional step before full installer packaging.
