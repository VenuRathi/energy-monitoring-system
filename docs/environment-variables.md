# Environment Variable Guide

This project reads runtime settings from `.env` through `config/settings.py`.

## Variables

### Database

- `DB_HOST`: PostgreSQL host
- `DB_PORT`: PostgreSQL port, usually `5432`
- `DB_NAME`: database name
- `DB_USER`: database login user
- `DB_PASSWORD`: database login password
- `DB_CONNECT_TIMEOUT_SECONDS`: PostgreSQL connection timeout in seconds

### Readings retention

- `READINGS_RETENTION_DAYS`: how many days of readings to keep; `0` disables automatic cleanup
- `READINGS_CLEANUP_BATCH_SIZE`: maximum old readings deleted in one cleanup pass
- `READINGS_CLEANUP_INTERVAL_HOURS`: minimum hours between cleanup attempts

### API

- `API_HOST`: Flask bind host
- `API_PORT`: Flask/API port
- `API_DEBUG`: set `true` only when intentionally debugging
- `API_ALLOWED_ORIGINS`: comma-separated CORS allowlist for the frontend
- `API_KEY_ENABLED`: enable or disable API key checks for protected write, control, email, and report download endpoints
- `API_KEY`: backend secret checked against `X-API-Key`

### Frontend

- `VITE_API_BASE_URL`: frontend API base URL override
- `VITE_API_KEY`: frontend API key header value for protected API actions and report downloads

### Runtime / polling

- `POLL_INTERVAL_SECONDS`: polling loop interval in seconds
- `DEMO_MODE`: serve synthetic data instead of requiring live meters
- `ENABLE_DATABASE`: toggle PostgreSQL usage
- `APP_TIMEZONE`: app display/report timezone, current default `Asia/Calcutta`

## Current frontend API URL behavior

- Dev with no `VITE_API_BASE_URL`: uses `http://127.0.0.1:5000`
- Production with no `VITE_API_BASE_URL`: uses relative `/api`
- If `VITE_API_BASE_URL` is set: it overrides the default

## Recommended values

## Local development

```dotenv
ENABLE_DATABASE=true
DEMO_MODE=false
POLL_INTERVAL_SECONDS=18
APP_TIMEZONE=Asia/Calcutta

API_HOST=127.0.0.1
API_PORT=5000
API_DEBUG=false
API_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
API_KEY_ENABLED=false
API_KEY=replace_me

VITE_API_BASE_URL=
VITE_API_KEY=

DB_HOST=localhost
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=postgres
DB_PASSWORD=replace_me
DB_CONNECT_TIMEOUT_SECONDS=5
READINGS_RETENTION_DAYS=1825
READINGS_CLEANUP_BATCH_SIZE=5000
READINGS_CLEANUP_INTERVAL_HOURS=1
```

## Boss demo on one laptop

If backend and frontend run on the same laptop:

```dotenv
ENABLE_DATABASE=true
DEMO_MODE=false
POLL_INTERVAL_SECONDS=18
APP_TIMEZONE=Asia/Calcutta

API_HOST=127.0.0.1
API_PORT=5000
API_DEBUG=false
API_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
API_KEY_ENABLED=false
API_KEY=replace_me

VITE_API_BASE_URL=
VITE_API_KEY=

DB_HOST=localhost
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=postgres
DB_PASSWORD=replace_me
DB_CONNECT_TIMEOUT_SECONDS=5
READINGS_RETENTION_DAYS=1825
READINGS_CLEANUP_BATCH_SIZE=5000
READINGS_CLEANUP_INTERVAL_HOURS=1
```

If you want API key mode enabled for the demo:

```dotenv
API_KEY_ENABLED=true
API_KEY=demo-secret-123
VITE_API_KEY=demo-secret-123
```

## Plant / local-network deployment

Example:

```dotenv
ENABLE_DATABASE=true
DEMO_MODE=false
POLL_INTERVAL_SECONDS=18
APP_TIMEZONE=Asia/Calcutta

API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=false
API_ALLOWED_ORIGINS=http://plant-pc:5173,http://192.168.1.50:5173
API_KEY_ENABLED=true
API_KEY=strong-random-secret

VITE_API_BASE_URL=http://plant-pc:5000
VITE_API_KEY=strong-random-secret

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=energy_user
DB_PASSWORD=replace_me
DB_CONNECT_TIMEOUT_SECONDS=5
READINGS_RETENTION_DAYS=1825
READINGS_CLEANUP_BATCH_SIZE=5000
READINGS_CLEANUP_INTERVAL_HOURS=1
```

## Important warnings

- `VITE_API_KEY` is embedded into the browser build. It is useful for controlled LAN deployments and demos, not as a replacement for real login/auth.
- `API_DEBUG` should stay `false` outside active local debugging.
- Keep `.env` out of source control.
- Restart the backend after changing `.env`.
- Rebuild the frontend after changing any `VITE_` variable.

## SMTP variables

These are also present in `.env.example` and are required if email/report delivery is used:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_USE_TLS`
- `SMTP_USE_SSL`

Production recommendation:

- Put the SMTP password in `SMTP_PASSWORD`.
- When `SMTP_PASSWORD` is set, it overrides any password saved through the UI/database.
- UI saves will not store a new plaintext password while `SMTP_PASSWORD` is active.
