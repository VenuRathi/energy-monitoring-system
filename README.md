# Energy Monitoring System

Industrial energy monitoring system for Schneider PM5000 / EM6400-class Modbus RTU meters with PostgreSQL storage, Flask API, React/Vite frontend, dashboarding, meter management, and document exports.

[![CI](https://github.com/VenuRathi/energy-monitoring-system/actions/workflows/ci.yml/badge.svg)](https://github.com/VenuRathi/energy-monitoring-system/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Current status

Current stabilized state after Phases 1-3:

- Python Modbus RTU polling running
- PostgreSQL persistence active
- Flask API active
- React/Vite frontend active
- `/api/status` runtime health available
- API key mode and CORS hardening available
- polling resilience improved for meter/COM/database failures

Healthy live target state:

- API ok
- Database ok
- Polling running
- `MTR-001` online
- `MTR-002` online
- `MTR-003` disabled/offline and not counted as stale
- `staleMeterCount = 0`

## Features

- Modbus RTU polling for Schneider PM5000 / EM6400-style meters
- PostgreSQL storage for meter definitions and readings
- Flask API for dashboard, meter management, reports, email settings, and status
- React frontend with dashboard, trends, reports, and meter pages
- In-app Help & Guide page for operators and support handover
- Excel export and Word report generation
- Optional API key protection for protected write/control/report/email endpoints
- Runtime heartbeat and per-meter status via `/api/status`

## Architecture

```text
Meters (PM5000/EM6400)
	-> Modbus RTU
	-> Python collectors and polling services
	-> PostgreSQL persistence and rules
	-> Flask API layer
	-> React dashboard and reporting UI
```

Mermaid diagram version: [docs/architecture.md](docs/architecture.md)

## Tech Stack

- Python 3.11+ (Python 3.13 currently validated)
- Flask
- PostgreSQL + psycopg
- pymodbus + pyserial
- React + TypeScript + Vite
- TanStack Query + Recharts

## Quick Start

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe main.py
```

Frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run dev
```

For full local setup details, see [docs/local-setup.md](docs/local-setup.md).

## Documentation package

- Production handover index: [docs/production-handover-index.md](docs/production-handover-index.md)
- Production deployment checklist: [docs/production-deployment-checklist.md](docs/production-deployment-checklist.md)
- 24/7 operations SOP: [docs/operations-sop-24x7.md](docs/operations-sop-24x7.md)
- Backup and restore SOP: [docs/backup-restore-sop.md](docs/backup-restore-sop.md)
- Incident response guide: [docs/incident-response-guide.md](docs/incident-response-guide.md)
- Production readiness signoff: [docs/production-readiness-signoff.md](docs/production-readiness-signoff.md)
- Local setup: [docs/local-setup.md](docs/local-setup.md)
- Environment variables: [docs/environment-variables.md](docs/environment-variables.md)
- Meter configuration: [docs/meter-configuration.md](docs/meter-configuration.md)
- Operations runbook: [docs/operations-runbook.md](docs/operations-runbook.md)
- PostgreSQL verification queries: [docs/postgresql-verification.md](docs/postgresql-verification.md)
- Boss demo script: [docs/boss-demo-script.md](docs/boss-demo-script.md)
- Deployment checklist: [docs/deployment-checklist.md](docs/deployment-checklist.md)
- Known limitations: [docs/known-limitations.md](docs/known-limitations.md)
- Plant PC deployment: [docs/plant-pc-deployment.md](docs/plant-pc-deployment.md)
- Task Scheduler setup: [docs/task-scheduler-setup.md](docs/task-scheduler-setup.md)
- Pilot checklist: [docs/pilot-checklist.md](docs/pilot-checklist.md)
- Backup and maintenance: [docs/backup-and-maintenance.md](docs/backup-and-maintenance.md)
- Release bundle workflow: [docs/release-bundle.md](docs/release-bundle.md)
- Pilot validation runbook: [docs/pilot-validation-runbook.md](docs/pilot-validation-runbook.md)
- Pilot validation results: [docs/pilot-validation-results.md](docs/pilot-validation-results.md)
- Pilot evidence log: [docs/pilot-evidence-log.md](docs/pilot-evidence-log.md)
- Windows installer workflow: [docs/windows-installer-workflow.md](docs/windows-installer-workflow.md)
- Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- Data model: [docs/data-model.md](docs/data-model.md)
- Engineering gap review: [docs/engineering-gap-review.md](docs/engineering-gap-review.md)
- Final 45-day plan: [docs/final-45-day-plan.md](docs/final-45-day-plan.md)
- OpenAPI starter contract: [docs/openapi.yaml](docs/openapi.yaml)

## Developer handover package

- Developer guide: [docs/developer-guide.md](docs/developer-guide.md)
- Codebase map: [docs/codebase-map.md](docs/codebase-map.md)
- Debugging guide: [docs/debugging-guide.md](docs/debugging-guide.md)
- Change guide: [docs/change-guide.md](docs/change-guide.md)
- Maintenance playbook: [docs/maintenance-playbook.md](docs/maintenance-playbook.md)

## Repository Layout

- `main.py`: backend runtime entrypoint and polling loop
- `run_app.bat`: Windows local app launcher that starts the backend if needed and opens the UI
- `app/collectors/`: Modbus client and Schneider decoding
- `app/services/`: polling orchestration
- `app/database/`: PostgreSQL connection, schema, repositories
- `app/api/`: Flask API routes and response shaping
- `config/`: runtime settings and meter configuration
- `frontend/`: Vite + React frontend
- `logs/`: backend runtime logs/artifacts
- `tests/`: smoke tests

## API Endpoints

- `GET /api/health`
- `GET /api/meters`
- `POST /api/meters`
- `PUT /api/meters/<meter_id>`
- `DELETE /api/meters/<meter_id>`
- `GET /api/parameters`
- `GET /api/dashboard`
- `GET /api/meters/<meter_id>/readings`
- `GET /api/meters/<meter_id>/trend`
- `POST /api/reports/excel`
- `POST /api/reports/word`
- `GET /api/email/settings`
- `POST /api/email/settings`
- `GET /api/email/health`
- `POST /api/email/test`

OpenAPI contract (starter): [docs/openapi.yaml](docs/openapi.yaml)

## Safety / deployment warning

This repository is now suitable for demo use and controlled local-network deployment preparation, but it is not a fully internet-hardened production platform yet.

Important limitations:

- API key mode is not full user authentication
- `VITE_API_KEY` is visible in browser builds
- runtime meter health state is in memory and resets on restart
- polling is sequential
- retention cleanup exists, but archive policy, backup verification, and log rotation still need operational ownership

See [docs/known-limitations.md](docs/known-limitations.md).

## Security and responsible use

- Never commit `.env` or real credentials.
- Treat database and SMTP credentials as secrets and rotate them if leaked.
- Keep this project private until you complete your public-release checklist.
- Review [SECURITY.md](SECURITY.md) before production deployment.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned milestones and next improvements.

## Contributing

Please review [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before opening a pull request.

## Changelog

Release history and notable updates are tracked in [CHANGELOG.md](CHANGELOG.md).

## Testing

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
