# Codebase Map

This document explains where major responsibilities live so a new developer can navigate the repository quickly.

## Top-level structure

| Path | Responsibility |
|---|---|
| `main.py` | Main runtime entrypoint, embedded API startup, polling loop, meter-service rebuilds, COM/bus validation |
| `run_app.bat` | Windows local app launcher that starts the backend if needed and opens the UI |
| `scripts/` | Service/task-run helper scripts for deployment |
| `app/` | Backend application code |
| `config/` | Runtime settings and meter template/config loading |
| `frontend/` | React/Vite frontend |
| `docs/` | Operator, deployment, and handover documentation |
| `tests/` | Basic unit/smoke tests |
| `utils/` | Shared utility helpers |

## Backend map

## `main.py`

Owns:

- process single-instance lock
- embedded Flask API startup
- database schema creation on startup
- loading runtime meters
- building shared Modbus clients
- validating shared bus settings
- duplicate `slave_id` detection on same COM port
- rebuilding polling services when meter definitions change
- polling loop heartbeat tracking
- scheduled report processing trigger

Touch this file when:

- changing process startup flow
- changing how meters are loaded/rebuilt
- changing shared bus validation
- changing service/task/runtime loop behavior

## `app/api/server.py`

Owns:

- Flask application factory
- endpoint route definitions
- API key protection decorator
- CORS behavior
- frontend static serving from `frontend/dist`

Touch this file when:

- adding endpoints
- changing API route behavior
- changing frontend-serving behavior
- changing request/response decorators

## `app/api/service.py`

Owns:

- API-facing business/data shaping logic
- dashboard aggregation
- meter CRUD service logic
- report/export generation
- email/report schedule logic
- `/api/status` data shaping
- many validation rules for frontend/API flows

Touch this file when:

- changing returned JSON payloads
- changing export/report logic
- changing meter validation
- changing runtime status shaping

Be careful:

- this file is large and central
- frontend contracts depend heavily on it

## `app/services/polling_service.py`

Owns:

- per-meter poll attempt lifecycle
- runtime status updates for each meter
- collector invocation
- reading save flow
- alert evaluation flow
- meter-level error isolation

Touch this file when:

- changing per-meter polling logic
- changing what counts as success/failure
- changing DB insert handling
- changing alert rule evaluation

## `app/collectors/modbus_client.py`

Owns:

- low-level Modbus serial client usage
- COM connection/reconnect behavior
- read failure logging
- repeated-error suppression

Touch this file when:

- changing retry/reconnect behavior
- changing low-level Modbus read behavior
- changing serial-connection handling

## `app/collectors/schneider/pm5000.py`

Owns:

- Schneider PM5000/EM6400 register decoding
- parameter reading strategy
- block prefetch behavior
- retry amplification prevention

Touch this file when:

- adding/changing register maps
- adding new decoded parameters
- changing block-read behavior

Be careful:

- this is hardware-map-sensitive code
- do not change casually without meter-map verification

## `app/database/models.py`

Owns:

- DB schema SQL
- readings table generation from parameter config
- indexes
- schema evolution behavior

Touch this file when:

- changing table/index creation
- adding migration-like schema behavior
- changing parameter-to-column mapping

## `app/database/repositories.py`

Owns:

- SQL read/write repository operations
- meter persistence
- reading inserts
- report schedule persistence
- email settings persistence

Touch this file when:

- changing raw SQL behavior
- optimizing DB access
- adding repository operations

## `app/database/connection.py`

Owns:

- psycopg connection creation from `Settings`

## `app/runtime_state.py`

Owns:

- shared Modbus client registry
- per-meter runtime status state
- polling loop heartbeat state

Touch this file when:

- changing `/api/status` runtime memory model
- changing heartbeat tracked fields

## `config/settings.py`

Owns:

- `.env` loading
- typed `Settings` object

## `config/meter_loader.py`

Owns:

- loading and normalizing `config/meter_config.json`
- parameter-set expansion

## `config/meter_config.json`

Owns:

- base meter templates
- parameter sets
- starter/default meter definitions

## Frontend map

## `frontend/src/app/App.tsx`

- app root

## `frontend/src/app/layout/AppShell.tsx`

- main application shell/navigation flow

## `frontend/src/pages/`

- `DashboardPage.tsx`: live dashboard composition
- `MetersPage.tsx`: meter management, discovery, alert rules
- `ReportsPage.tsx`: export, schedules, email settings

## `frontend/src/components/dashboard/`

- dashboard-specific visual sections such as cards, chart, selector, alerts, metrics

## `frontend/src/components/meters/`

- meter table/editor form and alert rules UI

## `frontend/src/components/reports/`

- report filters, schedules, email settings UI

## `frontend/src/components/common/`

- shared UI safety pieces like `AppErrorBoundary`

## `frontend/src/api/energyApi.ts`

- typed frontend API wrapper functions

## `frontend/src/api/httpClient.ts`

- fetch wrapper
- API base URL resolution
- API key header injection
- file download handling

## `frontend/src/hooks/`

- query hooks and mutation wiring for frontend data flow

## `frontend/src/types/energy.ts`

- frontend-side API contract types

## `frontend/src/styles/global.css`

- global styling

## Fast “where do I change X?” guide

| Change needed | Start here |
|---|---|
| Add/change API endpoint | `app/api/server.py`, then `app/api/service.py`, then frontend `energyApi.ts`/types |
| Change dashboard payload | `app/api/service.py` and frontend `types/energy.ts` |
| Change per-meter polling behavior | `app/services/polling_service.py` |
| Change Modbus connection/reconnect | `app/collectors/modbus_client.py` |
| Add new meter parameter decode | `config/meter_config.json`, `app/collectors/schneider/pm5000.py`, maybe DB/report/frontend mappings |
| Change DB schema/indexes | `app/database/models.py` |
| Change plant-PC startup flow | `main.py`, `run_app.bat`, `scripts/` |
| Change report generation | `app/api/service.py` and reports frontend components |

## Files to inspect before major changes

Before changing polling:

- `main.py`
- `app/services/polling_service.py`
- `app/collectors/modbus_client.py`
- `app/collectors/schneider/pm5000.py`
- `app/runtime_state.py`

Before changing frontend API behavior:

- `app/api/server.py`
- `app/api/service.py`
- `frontend/src/api/energyApi.ts`
- `frontend/src/api/httpClient.ts`
- `frontend/src/types/energy.ts`
