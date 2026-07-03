# Deployment Checklist

Use this checklist for a clean setup on a fresh machine.

## 1. Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+ (if using live database mode)

## 2. Clone and install

```powershell
git clone https://github.com/VenuRathi/energy-monitoring-system.git
cd energy-monitoring-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd frontend
npm ci
cd ..
```

## 3. Configure environment

```powershell
Copy-Item .env.example .env
```

Minimum edits in `.env`:
- `DEMO_MODE=true` for hardware-free demonstrations
- or `DEMO_MODE=false` with real DB + meter settings
- Update DB and SMTP credentials appropriately

## 4. Start services

Backend:
```powershell
run_app.bat
```

Frontend:
```powershell
cd frontend
npm run dev
```

## 5. Validate system

- `GET /api/health` returns status payload with checks.
- Dashboard loads and meter cards render.
- Trend chart and latest readings populate.
- Report export and email settings endpoints respond.

## 6. Security pre-go-live

- Confirm `.env` is not tracked.
- Rotate any leaked credentials.
- Keep branch protection enabled on `main`.
- Ensure CI and secret scan workflows are passing.

## 7. Release hygiene

- Update `CHANGELOG.md`.
- Tag release (`v0.x.y`).
- Add release notes and screenshots.
