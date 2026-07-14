# Plant PC Deployment Guide

This guide prepares the project for a 4-5 meter, 24/7 pilot deployment on one Windows plant PC connected to the RS485/USB converter.

## Recommended pilot topology

- One Windows plant PC
- One USB-to-RS485 converter connected to that PC
- 4-5 Schneider PM5000 / EM6400-style meters on the same RS485 bus
- PostgreSQL installed on the same plant PC
- Backend running continuously on the same plant PC
- Frontend built once and served by the backend from `frontend/dist`
- Dashboard opened from the same local/plant network

Recommended ports:

- Backend/API + built frontend: `5000`
- PostgreSQL: local-only `5432`

## Why this is the simplest pilot setup

- No cloud services
- No extra static frontend server required
- No Docker or Kubernetes overhead
- Frontend can be served directly by the Flask backend after build
- Easier to support on a Windows plant PC

## 1. Install Python

Install Python 3.13 from python.org on the plant PC.

Important:

- Add Python to PATH during install if possible
- Confirm after install:

```powershell
python --version
```

## 2. Install PostgreSQL

Install PostgreSQL 14+ on the same PC.

Recommended:

- Keep PostgreSQL listening on localhost only
- Do not expose the database to the whole plant network unless there is a very specific need

Create the database:

```sql
CREATE DATABASE energy_monitoring;
```

## 3. Copy the project to the plant PC

Use either:

- `git clone`
- or a controlled project folder copy

Recommended location:

```text
C:\EnergyMonitoring\energy-monitoring-system
```

## 4. Create the virtual environment

```powershell
cd C:\EnergyMonitoring\energy-monitoring-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Configure `.env`

```powershell
Copy-Item .env.example .env
```

Recommended pilot values:

```dotenv
ENABLE_DATABASE=true
DEMO_MODE=false
POLL_INTERVAL_SECONDS=180
APP_TIMEZONE=Asia/Calcutta

API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=false
API_ALLOWED_ORIGINS=http://PLANT_PC_IP:5000
API_KEY_ENABLED=true
API_KEY=replace_with_strong_random_secret

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=postgres
DB_PASSWORD=replace_me

VITE_API_BASE_URL=
VITE_API_KEY=replace_with_strong_random_secret
```

Notes:

- With the backend serving the built frontend, keeping `VITE_API_BASE_URL=` is correct.
- Same-origin `/api` behavior is the simplest pilot deployment model.
- `POLL_INTERVAL_SECONDS=180` is a practical 3-minute pilot value.

## 6. Verify COM port

On Windows:

1. Open Device Manager
2. Expand `Ports (COM & LPT)`
3. Confirm the RS485/USB adapter, for example `COM6`

Make sure:

- the adapter is stable
- the COM number is known
- no other tool is holding the port

## 7. Verify meter slave IDs

Before enabling all meters:

- confirm each physical meter address
- confirm all enabled meters on the same bus use unique `slave_id`
- confirm shared serial settings match

Current safe pilot pattern:

- `MTR-001` -> `COM6`, slave `1`
- `MTR-002` -> `COM6`, slave `2`
- `MTR-003` -> disabled unless physically connected
- `MTR-004` -> unique slave
- `MTR-005` -> unique slave

## 8. Build the frontend for production

```powershell
cd frontend
npm ci
npm run build
cd ..
```

The backend will serve `frontend/dist` automatically at `/`.

## 9. Start backend manually once

```powershell
.\.venv\Scripts\python.exe main.py
```

Then verify:

- `http://127.0.0.1:5000/api/health`
- `http://127.0.0.1:5000/api/status`
- `http://127.0.0.1:5000/`

What the backend now checks/logs at startup:

- whether `.env` is present
- whether `frontend/dist` exists
- current API/polling mode summary
- COM ports detected on the machine
- database preflight success if PostgreSQL is enabled
- validated enabled meter summary
- warnings for duplicate slave IDs or serial-setting conflicts

## 10. Firewall notes

Recommended:

- allow inbound TCP `5000` only from the plant/local network that should view the dashboard
- keep PostgreSQL on localhost only if possible
- do not open PostgreSQL to the general network

## 11. Local network access

If the plant PC IP is `192.168.1.50`, users can open:

```text
http://192.168.1.50:5000
```

That gives them:

- frontend
- dashboard
- API behind the same origin

## 12. Pilot acceptance target

Healthy state:

- API ok
- database ok
- polling running
- `MTR-001` online
- `MTR-002` online
- disabled/fake meters not counted stale
- logs rotating into `logs/energy_monitoring.log`
- startup warnings reviewed and understood if any appear

## 13. Optional release-bundle handoff

If you want to move a clean snapshot instead of cloning the full repo, create a bundle on the source machine:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_release_bundle.ps1
```

Then transfer the generated zip/folder from `release\`.

See:

- [release-bundle.md](release-bundle.md)
