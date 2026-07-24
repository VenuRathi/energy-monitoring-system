# Developer Guide

This guide is for the next developer who needs to run, debug, deploy, or extend this project after the original internship handoff.

## What this system is

This project is a local industrial energy monitoring system for Schneider PM5000 / EM6400-style meters.

Current architecture:

- Python backend runtime
- Modbus RTU polling via COM port
- PostgreSQL persistence
- Flask API
- React/Vite frontend
- Excel and Word report generation
- Plant-PC oriented deployment model

It is currently best treated as:

- a serious pilot-ready industrial monitoring platform
- not yet a fully productized commercial software package

## Primary runtime flow

High-level flow:

```text
Meters -> RS485 bus -> USB/RS485 converter -> Python polling -> PostgreSQL -> Flask API -> React frontend
```

Main control flow:

1. `main.py` loads settings and meter config
2. database tables are created/updated if needed
3. embedded Flask API starts in the same process
4. enabled meters are loaded
5. polling services are built for each valid enabled meter
6. polling loop runs continuously
7. readings are inserted into PostgreSQL
8. `/api/dashboard`, `/api/meters`, `/api/status`, and report endpoints serve the frontend and operators

## Tech stack

- Python 3.13 currently validated
- Flask
- psycopg
- pymodbus
- pyserial
- PostgreSQL
- React 19 + TypeScript + Vite
- TanStack Query
- Recharts

## Quick local run

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

Frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run dev
```

Frontend build for backend-served mode:

```powershell
cd frontend
npm run typecheck
npm run build
cd ..
python main.py
```

## Deployment model

Current intended deployment:

- one Windows plant/server PC
- one local PostgreSQL instance
- one direct USB/RS485 connection on that same PC
- backend runs continuously on that machine
- frontend can be served from backend after `frontend/dist` is built
- operators access over local network if needed

Recommended 24/7 run approach today:

- Task Scheduler using:
  - `scripts/run_backend_service.bat`
  - `scripts/run_backend_watchdog.ps1`
  - `scripts/install_task_scheduler_backend.ps1`

## Important docs to read next

Core docs:

- [architecture.md](architecture.md)
- [data-model.md](data-model.md)
- [local-setup.md](local-setup.md)
- [environment-variables.md](environment-variables.md)
- [meter-configuration.md](meter-configuration.md)
- [operations-runbook.md](operations-runbook.md)
- [plant-pc-deployment.md](plant-pc-deployment.md)

Developer-handover docs:

- [codebase-map.md](codebase-map.md)
- [debugging-guide.md](debugging-guide.md)
- [change-guide.md](change-guide.md)
- [maintenance-playbook.md](maintenance-playbook.md)

## Environment/config model

Main runtime configuration comes from:

- `.env`
- `config/settings.py`

Meter templates/defaults come from:

- `config/meter_config.json`
- `config/meter_loader.py`

Database-stored meter records can override file defaults at runtime.

That means:

- `config/meter_config.json` is the base/template source
- `meters` table becomes the live runtime source once records exist in PostgreSQL

## Current design decisions that matter

### 1. Embedded API

The backend process and Flask API run in the same Python process.

Why that matters:

- simpler deployment
- simpler plant-PC pilot setup
- if the runtime dies, API and polling die together

### 2. Shared Modbus clients per bus

Meters sharing the same serial settings on the same COM port share a client.

Why that matters:

- more realistic RS485-bus behavior
- duplicate/conflicting settings must be validated carefully

### 3. Database schema is config-driven for readings columns

The `readings` table expands based on configured parameters.

Why that matters:

- parameter-name changes can affect DB columns
- do not casually rename existing parameters after data already exists

### 4. Runtime state is in memory

Per-meter polling health and loop heartbeat are stored in memory only.

Why that matters:

- `/api/status` resets after backend restart
- this is acceptable for the pilot, but not full long-term operational history

## What not to casually change

- Modbus register decoding in `app/collectors/schneider/pm5000.py`
- parameter names that already map to readings table columns
- database schema assumptions in `app/database/models.py`
- shared-bus validation logic in `main.py`
- `/api/status` shape unless frontend/docs are reviewed too

## How to think about future work

Short-term:

- UI polish
- developer handover completeness
- better release packaging

Medium-term:

- Windows installer
- auth/admin improvements
- backup automation

Long-term:

- stronger productization
- installer signing
- retention automation
- richer support tooling
