# Deployment Checklist

Use this before a boss demo, pilot deployment, or plant-side local-network setup.

## 1. Python environment

- [ ] Python 3.13 installed (or another validated 3.11+ interpreter)
- [ ] Virtual environment created
- [ ] `pip install -r requirements.txt` completed without errors
- [ ] Backend starts with `.\.venv\Scripts\python.exe main.py`

## 2. Frontend environment

- [ ] Node.js 20+ installed
- [ ] `cd frontend && npm ci` completed
- [ ] `cd frontend && npm run typecheck` passes
- [ ] `cd frontend && npm run build` passes

## 2A. Release / installer handoff

- [ ] `powershell -ExecutionPolicy Bypass -File .\scripts\prepare_release_bundle.ps1` completed
- [ ] `powershell -ExecutionPolicy Bypass -File .\scripts\validate_release_bundle.ps1 -RequireZip` passes
- [ ] If building installer, Inno Setup 6 installed
- [ ] If building installer, `powershell -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1` passes

## 3. PostgreSQL database

- [ ] PostgreSQL running
- [ ] Database created
- [ ] `.env` DB settings verified
- [ ] Backend creates/updates tables successfully on startup
- [ ] Latest readings can be queried in PostgreSQL

## 4. `.env` configuration

- [ ] `ENABLE_DATABASE` correct for the target environment
- [ ] `DEMO_MODE=false` for real meter operation
- [ ] `API_HOST` and `API_PORT` correct
- [ ] `API_DEBUG=false`
- [ ] `API_ALLOWED_ORIGINS` matches the frontend URL(s)
- [ ] `POLL_INTERVAL_SECONDS` verified
- [ ] `APP_TIMEZONE` verified
- [ ] `.env` exists on the plant PC and is not accidentally relying on defaults

## 5. API key mode

- [ ] Decide whether `API_KEY_ENABLED` is on or off
- [ ] If enabled, `API_KEY` is set
- [ ] If frontend writes are used, `VITE_API_KEY` matches `API_KEY`

## 6. CORS allowed origins

- [ ] Local dev URLs included if needed
- [ ] Plant/demo frontend URL included
- [ ] No wildcard origin fallback relied on

## 7. COM port verification

- [ ] Correct COM port confirmed in Device Manager
- [ ] No other application is holding the port
- [ ] USB-to-RS485 adapter is stable and recognized

## 8. Meter verification

- [ ] Meter slave IDs verified physically
- [ ] `MTR-001` reads successfully
- [ ] `MTR-002` reads successfully
- [ ] `MTR-003` disabled if not physically connected
- [ ] Shared-bus serial settings match across enabled meters on one COM port

## 9. Modbus test

- [ ] Backend logs show polling cycles running
- [ ] Startup logs show the expected detected COM port(s)
- [ ] Startup logs show the expected validated enabled meter list
- [ ] `/api/status` shows polling heartbeat
- [ ] Enabled live meters report `communicationStatus=online`
- [ ] `staleMeterCount=0` for the current healthy demo state

## 10. Dashboard test

- [ ] Frontend opens successfully
- [ ] Dashboard loads without white screen
- [ ] Meter selector works
- [ ] Latest readings visible for `MTR-001`
- [ ] Latest readings visible for `MTR-002`
- [ ] Disabled meter does not break dashboard behavior

## 11. Report/export test

- [ ] Excel export works for a recent range with data
- [ ] Word export works for a recent range with data
- [ ] Empty/invalid range errors are clear

## 12. Network / firewall setup

- [ ] API port reachable from the frontend machine if split across devices
- [ ] PostgreSQL reachable if not on the same machine
- [ ] Firewall rules documented
- [ ] Deployment remains on a controlled network

## 13. Logging and backup plan

- [ ] `logs/` folder reviewed
- [ ] Log cleanup/rotation plan defined
- [ ] PostgreSQL backup method agreed
- [ ] Recovery owner identified

## 14. Final handover test

- [ ] `GET /api/health` ok
- [ ] `GET /api/status` ok
- [ ] `MTR-001` online
- [ ] `MTR-002` online
- [ ] `MTR-003` disabled/offline and not counted stale
- [ ] Boss demo flow rehearsed once from start to finish
