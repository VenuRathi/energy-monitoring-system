# Local Setup Guide

This guide is for running the current system on a Windows development machine with PostgreSQL and real or demo meters.

## Prerequisites

- Windows 10/11
- Python 3.13 recommended for the current validated Windows setup
- Node.js 20+ recommended
- PostgreSQL 14+ recommended
- Access to the required COM port if using real meters

## 1. Clone and open the project

```powershell
git clone <your-repo-url>
cd energy-monitoring-system
```

## 2. Create the Python virtual environment

Recommended:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_python_env.ps1
```

Manual fallback:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `.venv` exists but is broken, recreate it:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_python_env.ps1 -Recreate
```

## 3. Create `.env`

```powershell
Copy-Item .env.example .env
```

Minimum local values for live mode:

```dotenv
ENABLE_DATABASE=true
DEMO_MODE=false
DB_HOST=localhost
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=postgres
DB_PASSWORD=your_password
API_HOST=127.0.0.1
API_PORT=5000
API_DEBUG=false
API_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
API_KEY_ENABLED=false
POLL_INTERVAL_SECONDS=18
APP_TIMEZONE=Asia/Calcutta
```

For hardware-free UI/demo testing:

```dotenv
DEMO_MODE=true
ENABLE_DATABASE=false
```

## 4. Set up PostgreSQL

Open `psql` or pgAdmin and create the database:

```sql
CREATE DATABASE energy_monitoring;
```

If you want a dedicated user:

```sql
CREATE USER energy_user WITH PASSWORD 'replace_me';
GRANT ALL PRIVILEGES ON DATABASE energy_monitoring TO energy_user;
```

Then update `.env`:

```dotenv
DB_NAME=energy_monitoring
DB_USER=energy_user
DB_PASSWORD=replace_me
```

Notes:

- The backend creates/updates the required tables on startup.
- Do not manually create the schema unless you are intentionally inspecting or restoring it.

## 5. Start the backend

Recommended:

```powershell
.\.venv\Scripts\python.exe main.py
```

Or use the bundled Windows launcher:

```powershell
run_app.bat
```

Backend default URL:

```text
http://127.0.0.1:5000
```

## 6. Start the frontend

```powershell
cd frontend
npm ci
npm run typecheck
npm run dev
```

Frontend default URL:

```text
http://127.0.0.1:5173
```

## 7. Build the frontend

```powershell
cd frontend
npm run typecheck
npm run build
```

## 8. Verify the system

Open:

- `http://127.0.0.1:5000/api/health`
- `http://127.0.0.1:5000/api/status`
- `http://127.0.0.1:5173`

Expected healthy live status:

- API ok
- Database ok
- Polling running
- MTR-001 online
- MTR-002 online
- MTR-003 disabled/offline and not counted as stale
- `staleMeterCount = 0`

## Common setup mistakes

- Wrong Python interpreter instead of `.venv\Scripts\python.exe`
- `.venv` exists but points to an invalid old Python install
- PostgreSQL service not started
- `.env` edited but backend not restarted
- Wrong `DB_PASSWORD`
- `API_ALLOWED_ORIGINS` missing the frontend URL
- Another app such as QModMaster locking `COM6`
- Meter connected physically but wrong `slave_id`
- Meter enabled in software but not actually powered/connected
- Trying to use `VITE_API_BASE_URL` for local dev when the default local behavior already works
- Leaving `DEMO_MODE=true` while expecting live meter data

## Local run commands summary

Backend:

```powershell
.\.venv\Scripts\python.exe main.py
```

Frontend:

```powershell
cd frontend
npm run dev
```

Frontend production build:

```powershell
cd frontend
npm run build
```
