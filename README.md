# Energy Monitoring System

Production-style full-stack energy monitoring platform for Schneider PM5000 / EM6400 class meters.

[![CI](https://github.com/VenuRathi/energy-monitoring-system/actions/workflows/ci.yml/badge.svg)](https://github.com/VenuRathi/energy-monitoring-system/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Why this project stands out

- Real meter polling using Modbus RTU
- Live backend API with dashboard, trend, and alert workflows
- Report generation (Excel and Word exports)
- Email settings and scheduled report delivery
- Full frontend experience with React + TypeScript

## Use Cases

- Industrial panel-level energy visibility
- Campus and facility energy monitoring
- Preventive alerting for abnormal load patterns
- Scheduled operational reporting for teams

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

## Demo and Screenshots

- Add screenshots to `docs/screenshots/` and reference them here.
- Add a short walkthrough video (2-4 minutes) showing:
  - meter discovery and setup
  - dashboard and trends
  - alerts and report scheduling

This section is intentionally prepared so your project looks strong for portfolio and review panels.

## Tech Stack

- Python 3.11+
- Flask
- PostgreSQL + psycopg
- pymodbus + pyserial
- React + TypeScript + Vite
- TanStack Query + Recharts

## Repository Layout

- `main.py`: backend runtime entrypoint and polling loop
- `run_app.bat`: Windows startup script for backend
- `app/collectors/`: Modbus client and Schneider register decoding
- `app/services/`: polling service orchestration
- `app/database/`: PostgreSQL connection, schema, repositories
- `app/api/`: Flask API routes and response shaping
- `config/`: meter definitions and runtime settings loader
- `frontend/`: Vite + React frontend
- `sql/`: optional database views for dashboard/reporting
- `tests/`: smoke tests

## Quick Start

1. Clone repository.
2. Create Python virtual environment and install backend dependencies.
3. Copy `.env.example` to `.env` and fill your local values.
4. Start backend and frontend.

For demo/presentation without physical meters, set `DEMO_MODE=true` in `.env`.

### Backend Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
run_app.bat
```

### Frontend Setup

```powershell
cd frontend
npm ci
npm run dev
```

Frontend default URL:

```text
http://127.0.0.1:5173
```

## Environment Variables

Use `.env.example` as the source of truth for required keys.

Important values:

- `ENABLE_DATABASE`, `POLL_INTERVAL_SECONDS`, `APP_TIMEZONE`
- `DEMO_MODE` (set `true` to run without hardware and serve synthetic data)
- `API_HOST`, `API_PORT`, `CORS_ALLOWED_ORIGINS`
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`

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

## Data Model

Database model overview: [docs/data-model.md](docs/data-model.md)

## Deployment Checklist

Fresh machine bootstrap and deployment notes: [docs/deployment-checklist.md](docs/deployment-checklist.md)

## Security and Responsible Use

- Never commit `.env` or real credentials.
- Treat database and SMTP credentials as secrets and rotate them if leaked.
- Keep this project private until you complete your public-release checklist.
- Review [SECURITY.md](SECURITY.md) before production deployment.

## Feedback and Suggestions

I welcome feedback from visitors, reviewers, and collaborators.

- Feature ideas and improvements: open a Feature Request issue.
- Bugs and reliability concerns: open a Bug Report issue.
- Questions and guidance requests: open a Question issue.
- General discussion and project conversation: use GitHub Discussions (recommended).

If discussions are not enabled yet, open a Question issue and it will be redirected.

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
