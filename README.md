# Energy Monitoring System

Local-first IIoT energy monitoring platform for Schneider PM5000 / EM6400-class Modbus RTU meters.

[![CI](https://github.com/VenuRathi/energy-monitoring-system/actions/workflows/ci.yml/badge.svg)](https://github.com/VenuRathi/energy-monitoring-system/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20Plant%20PC-blue.svg)](#deployment-model)
[![Status](https://img.shields.io/badge/status-pilot--ready%20with%20conditions-orange.svg)](docs/production-readiness-signoff.md)

## Overview

Energy Monitoring System is a plant-floor monitoring application that collects live electrical measurements from energy meters over RS485/Modbus RTU, stores them in PostgreSQL, and exposes dashboards, trends, reports, alerts, and health checks through a local web interface.

It is designed for supervised industrial pilot deployment on a Windows plant PC or local server. The architecture keeps data local, avoids cloud dependency, and includes practical handover material for operators, maintenance staff, and future developers.

## What It Does

- Polls Schneider PM5000 / EM6400-style meters over Modbus RTU.
- Stores meter definitions, readings, alerts, schedules, and settings in PostgreSQL.
- Shows live meter status, latest readings, trends, alarms, and data quality in a React dashboard.
- Generates Excel and Word reports from historical readings.
- Provides API health, runtime polling status, per-meter communication state, and backend logs.
- Supports Windows Task Scheduler startup, local backups, release bundles, and plant handover SOPs.

## Why This Project Matters

Industrial monitoring software is judged by what happens after the demo: stale meters, COM-port changes, database outages, bad timestamps, restarts after power failure, and maintainability after handover.

This project focuses on those real plant concerns:

- **Local resilience:** continues operating on the plant LAN without cloud services.
- **Operational visibility:** exposes `/api/status`, per-meter stale state, logs, and health scripts.
- **Data integrity:** uses PostgreSQL persistence, duplicate-reading protection, retention controls, and report row limits.
- **Handover readiness:** includes deployment, backup/restore, incident response, debugging, and maintenance guides.
- **Practical product path:** supports developer-style deployment today and documents the route toward a Windows-installable product.

## Current Status

Current GitHub release point: `Version : 2`

Readiness classification:

> **Production-ready with conditions** for controlled plant pilot use.

Validated capabilities include:

- live Python backend and React frontend
- PostgreSQL-backed meter/readings storage
- Modbus RTU polling with runtime meter health
- API key protection for protected write/control/report/email endpoints
- report export hardening
- readings retention cleanup
- backup and scheduled-task scripts
- professional deployment and operations handover docs

Remaining production conditions are tracked in [docs/production-readiness-signoff.md](docs/production-readiness-signoff.md).

## Architecture

```text
Energy meters
  Schneider PM5000 / EM6400-style devices
  RS485 bus / USB serial COM adapter
        |
        v
Collector layer
  pymodbus + pyserial
  meter driver decoding
  polling loop and retry behavior
        |
        v
Persistence layer
  PostgreSQL schema
  readings, meters, alerts, schedules
  duplicate protection and retention cleanup
        |
        v
Backend API
  Flask routes
  dashboard data, status, reports, email, meter management
        |
        v
Operator UI
  React + TypeScript + Vite
  dashboard, meters, reports, help, status views
```

Mermaid architecture reference: [docs/architecture.md](docs/architecture.md)

## Feature Highlights

### Industrial Data Acquisition

- Modbus RTU polling over Windows COM ports
- per-meter slave ID configuration
- Schneider PM5000 / EM6400-style register map
- live communication status, stale detection, and failure counters
- resilience against disconnected or unavailable COM ports

### Dashboard And Operator UI

- live dashboard summary
- meter cards and meter table
- data quality indicators
- trend visualization
- report filters and export workflow
- in-app Help & Guide page for operators

### Reporting

- Excel report export
- Word report export
- scheduled report support
- email report workflow
- protected report download endpoints when API key mode is enabled

### Operations And Deployment

- Windows plant PC deployment checklist
- Task Scheduler backend startup
- daily backup task script
- runtime health check script
- PostgreSQL backup and restore SOP
- incident response guide
- production readiness signoff checklist

## Tech Stack

| Area | Technology |
| --- | --- |
| Backend | Python 3.11+, Flask |
| Meter communication | pymodbus, pyserial, Modbus RTU |
| Database | PostgreSQL, psycopg |
| Frontend | React, TypeScript, Vite |
| Data UI | TanStack Query, Recharts |
| Reports | Excel and Word document generation |
| Runtime | Windows plant PC/server, Task Scheduler |

## Repository Tour

| Path | Purpose |
| --- | --- |
| `main.py` | Runtime entrypoint, backend startup, polling orchestration |
| `app/collectors/` | Modbus client and Schneider meter driver |
| `app/services/` | Polling and retention services |
| `app/database/` | PostgreSQL schema, connection, repositories |
| `app/api/` | Flask routes and API service logic |
| `frontend/` | React/Vite operator interface |
| `config/` | Meter configuration and runtime defaults |
| `scripts/` | Windows setup, health, backup, startup, release scripts |
| `docs/` | Deployment, operations, handover, architecture, and troubleshooting docs |
| `tests/` | Backend smoke and behavior tests |

## Quick Start

### 1. Backend

```powershell
cd D:\FFPL\energy-monitoring-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe main.py
```

### 2. Frontend Development Server

```powershell
cd frontend
npm ci
npm run typecheck
npm run dev
```

For full setup instructions, use [docs/local-setup.md](docs/local-setup.md).

## Deployment Model

The intended plant deployment is local:

- Windows plant PC or local server
- PostgreSQL installed locally
- backend running through Windows Task Scheduler
- built frontend served by the backend on port `5000`
- meters connected through USB-to-RS485 COM ports
- access limited to the approved plant LAN

Primary deployment guide: [docs/production-deployment-checklist.md](docs/production-deployment-checklist.md)

## Health Check

After starting the backend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_runtime_health.ps1 -MinimumExpectedEnabledMeters 2
```

A healthy pilot run should show:

- API status `ok`
- database status `ok`
- polling running
- expected enabled meters online
- no stale enabled meters

## Documentation

Start here:

- [Production handover index](docs/production-handover-index.md)
- [Production deployment checklist](docs/production-deployment-checklist.md)
- [24/7 operations SOP](docs/operations-sop-24x7.md)
- [Backup and restore SOP](docs/backup-restore-sop.md)
- [Incident response guide](docs/incident-response-guide.md)
- [Production readiness signoff](docs/production-readiness-signoff.md)

Developer references:

- [Developer guide](docs/developer-guide.md)
- [Codebase map](docs/codebase-map.md)
- [Debugging guide](docs/debugging-guide.md)
- [Change guide](docs/change-guide.md)
- [Maintenance playbook](docs/maintenance-playbook.md)
- [OpenAPI starter contract](docs/openapi.yaml)

Setup and operations:

- [Environment variables](docs/environment-variables.md)
- [Meter configuration](docs/meter-configuration.md)
- [Task Scheduler setup](docs/task-scheduler-setup.md)
- [Plant PC deployment](docs/plant-pc-deployment.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Release bundle workflow](docs/release-bundle.md)
- [Windows installer workflow](docs/windows-installer-workflow.md)

## API Snapshot

Common endpoints:

- `GET /api/health`
- `GET /api/status`
- `GET /api/meters`
- `POST /api/meters`
- `PUT /api/meters/<meter_id>`
- `GET /api/dashboard`
- `GET /api/meters/<meter_id>/readings`
- `GET /api/meters/<meter_id>/trend`
- `POST /api/reports/excel`
- `POST /api/reports/word`
- `GET /api/email/health`

Full starter contract: [docs/openapi.yaml](docs/openapi.yaml)

## Testing

Backend tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Frontend checks:

```powershell
cd frontend
npm run typecheck
npm run build
```

## Safety And Security

This system is built for controlled local-network deployment, not direct internet exposure.

Important notes:

- API key mode is not a replacement for full user authentication.
- `VITE_API_KEY` is visible in browser builds.
- Keep `.env`, database credentials, SMTP credentials, backups, and plant network details private.
- Restrict port `5000` to approved plant LAN clients.
- Review [SECURITY.md](SECURITY.md) before broader rollout.

Known limitations and future production conditions: [docs/known-limitations.md](docs/known-limitations.md)

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned improvements.

High-value next steps:

- plant soak-test evidence
- backup/restore proof
- installer packaging
- stronger authentication and roles
- archive-before-delete option for compliance-driven plants
- signed release and upgrade workflow

## Suggested Showcase Additions

To make the repository feel even more polished on GitHub:

- add dashboard screenshots under `docs/assets/screenshots/`
- add a short demo GIF showing dashboard, meters, and report export
- add a one-page architecture image for management presentations
- add sample anonymized report exports
- add a `v2.0.0` GitHub release with release notes and deployment checklist links
- add a short project demo video or LinkedIn portfolio write-up

## Contributing

Please review [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md) before opening a pull request or issue.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
