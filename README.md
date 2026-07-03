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
- Excel export and Word report generation
- Optional API key protection for write/control endpoints
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

- Python 3.11+
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
npm run dev
```

For full local setup details, see [docs/local-setup.md](docs/local-setup.md).

## Documentation package

- Local setup: [docs/local-setup.md](docs/local-setup.md)
- Environment variables: [docs/environment-variables.md](docs/environment-variables.md)
- Meter configuration: [docs/meter-configuration.md](docs/meter-configuration.md)
- Operations runbook: [docs/operations-runbook.md](docs/operations-runbook.md)
- PostgreSQL verification queries: [docs/postgresql-verification.md](docs/postgresql-verification.md)
- Boss demo script: [docs/boss-demo-script.md](docs/boss-demo-script.md)
- Deployment checklist: [docs/deployment-checklist.md](docs/deployment-checklist.md)
- Known limitations: [docs/known-limitations.md](docs/known-limitations.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- Data model: [docs/data-model.md](docs/data-model.md)
- OpenAPI starter contract: [docs/openapi.yaml](docs/openapi.yaml)

## Repository Layout

- `main.py`: backend runtime entrypoint and polling loop
- `run_app.bat`: Windows backend launcher
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
- retention/archival/log rotation policies still need operational ownership

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
