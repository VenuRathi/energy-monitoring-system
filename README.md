# Energy Monitoring System

Real-time energy monitoring pipeline for Schneider PM5000 / EM6400 style meters.

## Current Architecture

Schneider Meter
-> Modbus RTU
-> Python Collector
-> Polling Service
-> PostgreSQL
-> Flask API
-> React Frontend

## Tech Stack

- Python 3
- Flask
- PostgreSQL
- psycopg 3
- pymodbus
- pyserial
- React
- TypeScript
- Vite
- TanStack Query
- Recharts

## Project Layout

- `main.py`: backend runtime entrypoint and polling loop
- `run_app.bat`: Windows startup script for the backend
- `app/collectors/`: Modbus client and Schneider register decoding
- `app/services/`: polling service orchestration
- `app/database/`: PostgreSQL connection, schema, repositories
- `app/api/`: Flask API routes and response shaping
- `config/`: `.env` settings and meter/register config
- `frontend/`: Vite + React frontend
- `sql/`: optional database views for dashboard/reporting
- `tests/`: lightweight smoke tests

## Runtime Notes

- Meter register definitions remain in `config/meter_config.json`.
- Meter connection settings are stored in PostgreSQL and refreshed by the backend.
- Only one backend instance should run at a time.
- The backend and frontend are both designed for local-network or local-machine use.

## Environment

Create a `.env` file with values like:

```env
ENABLE_DATABASE=true
POLL_INTERVAL_SECONDS=18

API_HOST=127.0.0.1
API_PORT=5000
API_DEBUG=false
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

DB_HOST=localhost
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=postgres
DB_PASSWORD=postgres

SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=alerts@example.com
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

## Run Backend

Preferred on Windows:

```powershell
run_app.bat
```

Manual start:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Run Frontend

```powershell
cd frontend
npm run dev
```

Open the printed Vite URL, usually:

```text
http://127.0.0.1:5173
```

## Run API Only

```powershell
.\.venv\Scripts\python.exe -m app.api.server
```

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

## Tests

Run the smoke tests with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```
