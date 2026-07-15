# Pilot Checklist

Use this for the final 4-5 meter pilot readiness review on the plant PC.

## System

- [ ] Windows plant PC is stable and dedicated for this pilot
- [ ] UPS/power reliability considered if needed
- [ ] Python installed
- [ ] PostgreSQL installed
- [ ] Project copied to the plant PC
- [ ] `.venv` created
- [ ] `pip install -r requirements.txt` completed

## Configuration

- [ ] `.env` created from `.env.example`
- [ ] `ENABLE_DATABASE=true`
- [ ] `DEMO_MODE=false`
- [ ] `API_DEBUG=false`
- [ ] `API_KEY_ENABLED=true`
- [ ] `API_KEY` set
- [ ] `API_ALLOWED_ORIGINS` restricted to the plant frontend URL
- [ ] `POLL_INTERVAL_SECONDS=180` or other deliberate pilot value

## Meter configuration

- [ ] 4-5 real meters only
- [ ] all enabled meters on the same COM port use matching serial settings
- [ ] each enabled meter on the same COM port has a unique `slave_id`
- [ ] fake/template meters disabled
- [ ] `MTR-003` disabled unless physically present

## Frontend

- [ ] `npm ci` completed
- [ ] `npm run typecheck` completed
- [ ] `npm run build` completed
- [ ] backend serves the built frontend from `frontend/dist`

## Release handoff

- [ ] release bundle created if this pilot will be transferred as a package
- [ ] release bundle validation passes
- [ ] installer compiled if software-style install is required for the target PC

## Runtime

- [ ] backend starts manually
- [ ] scheduled task starts backend automatically
- [ ] backend restarts after reboot
- [ ] logs are written to `logs/energy_monitoring.log`
- [ ] log rotation active
- [ ] startup preflight logs reviewed once after deployment

## Health

- [ ] `/api/health` reachable
- [ ] `/api/status` reachable
- [ ] polling heartbeat visible
- [ ] uptime field visible
- [ ] cycle count increasing
- [ ] `MTR-001` online
- [ ] `MTR-002` online
- [ ] any disabled meter not counted stale

## Database

- [ ] new readings appear in PostgreSQL
- [ ] row counts increase over time
- [ ] database backup plan agreed
- [ ] daily backup script tested once
- [ ] backup task installed if required

## Network

- [ ] frontend/API reachable from the intended local network
- [ ] firewall open only for the required frontend/API port
- [ ] PostgreSQL not exposed to the full network if avoidable

## Final go/no-go

- [ ] one cold reboot tested
- [ ] one COM disconnect/reconnect test done
- [ ] one wrong meter/disabled meter test done
- [ ] one PostgreSQL outage recovery test done
- [ ] one export test done
- [ ] one `/api/status` review done with operators
- [ ] [pilot-validation-runbook.md](pilot-validation-runbook.md) completed or reviewed
