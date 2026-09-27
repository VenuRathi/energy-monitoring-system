# Energy Monitoring System

**Local-first energy monitoring for industrial sites.** Collect electrical readings from Modbus RTU meters, track equipment and data health, and produce reports from a Windows plant PC or local server.

[![CI](https://github.com/VenuRathi/energy-monitoring-system/actions/workflows/ci.yml/badge.svg)](https://github.com/VenuRathi/energy-monitoring-system/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%7C%20TypeScript-3178C6.svg)](frontend/)

## Project status

The repository contains the application, deployment tooling, CI, and operator/developer documentation for a **supervised plant pilot**. Full production signoff depends on site evidence such as a sustained soak test, restart recovery, database outage recovery, and verified backup restoration. See the [readiness checklist](docs/handover/production-readiness-signoff.md) for the current acceptance criteria.

This is a monitoring and reporting system. It is intended for a controlled local network and is not designed to be exposed directly to the public internet.

## At a glance

- Poll configured Schneider PM5000/EM6400-family meters over RS485 and Modbus RTU.
- Persist readings and operational data in PostgreSQL; buffer readings locally during database outages for later replay.
- View meter readings, trends, freshness, communication state, and alerts in a React dashboard.
- Export historical readings to Excel and Word, with scheduled report and email workflows.
- Deploy and operate on Windows with health checks, backup scripts, release tooling, and handover procedures.

## Architecture

![System architecture: Modbus meters feed the local collector and PostgreSQL-backed Flask API, which serves the React dashboard and report workflows.](docs/assets/architecture.svg)

The API is the integration boundary between acquisition and the browser UI. The system can also run in demo mode with synthetic data; live meter operation requires site-specific configuration and hardware validation.

## Technology

| Layer | Implementation |
| --- | --- |
| Meter interface | RS485, Modbus RTU, `pymodbus`, `pyserial` |
| Backend | Python, Flask |
| Persistence | PostgreSQL, with a bounded local SQLite reading spool |
| Operator interface | React, TypeScript, Vite, TanStack Query, Recharts |
| Reports | Excel and Word exports |
| Target runtime | Windows plant PC or local server |

## Getting started

Use the [local development setup](docs/developer/local-setup.md) for the complete prerequisites and configuration steps. The application needs a configured database; live polling additionally requires a correctly wired meter and verified serial settings.

At a high level, local development uses Python 3.11+, Node.js, and PostgreSQL:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Then follow the setup guide to configure PostgreSQL and meter settings before starting the backend and frontend. Do not copy real plant names, COM-port mappings, credentials, or network details into public examples.

## Repository map

| Path | Purpose |
| --- | --- |
| `app/collectors/` | Modbus client and meter drivers |
| `app/services/` | Polling, durable reading spool, retention, and report worker |
| `app/database/` | PostgreSQL schema and repository access |
| `app/api/` | Flask routes and service logic |
| `frontend/` | React and TypeScript operator interface |
| `deployment/`, `scripts/` | Windows setup, health, backup, release, and validation tooling |
| `docs/` | Architecture, developer guides, deployment, and handover procedures |
| `tests/` | Backend behavior and regression tests |

## Validation commands

Run the same checks used by CI from the repository root:

```powershell
python scripts/validate_repository.py
python -m unittest discover -s tests
```

```powershell
Set-Location frontend
npm ci
npm run build
```

These checks validate code and packaging behavior. They do not replace commissioning tests with the actual plant PC, meter wiring, database, and operating procedures.

## Documentation

| If you are… | Start here |
| --- | --- |
| Setting up a development environment | [Local setup](docs/developer/local-setup.md) |
| Learning how the code is organized | [Codebase map](docs/developer/codebase-map.md) |
| Deploying at a site | [Production deployment checklist](docs/handover/production-deployment-checklist.md) |
| Operating or recovering the service | [24/7 operations SOP](docs/handover/operations-sop-24x7.md) and [incident response](docs/handover/incident-response-guide.md) |
| Protecting and restoring data | [Backup and restore SOP](docs/handover/backup-restore-sop.md) |
| Reviewing remaining acceptance work | [Production readiness signoff](docs/handover/production-readiness-signoff.md) |
| Configuring meters and environment | [Meter configuration](docs/reference/meter-configuration.md) and [environment variables](docs/reference/environment-variables.md) |
| Reviewing API shapes | [OpenAPI starter contract](docs/reference/openapi.yaml) |

See the [documentation index](docs/README.md) for the full collection.

## Security and deployment notes

- Keep `.env`, credentials, database backups, plant network details, and site-specific meter configuration private.
- The optional API key protects selected endpoints; it is not a user authentication or role system. A frontend API key is visible to browser users.
- Restrict network access to approved local clients and review [SECURITY.md](SECURITY.md) before deployment.
- Follow the deployment checklist and validate the target site; a successful CI run alone does not establish plant readiness.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change. Security issues should follow the private reporting instructions in [SECURITY.md](SECURITY.md).

## License

Distributed under the [MIT License](LICENSE).
