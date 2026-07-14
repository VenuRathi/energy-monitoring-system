# Change Guide

This guide explains how to make changes safely without breaking live polling, stored data, or frontend/backend contracts.

## Safe change principles

Before changing anything, ask:

1. Does this affect live polling?
2. Does this affect stored DB schema or column names?
3. Does this change API response shape?
4. Does the frontend assume the old shape?
5. Does this require hardware verification?

## What not to casually change

- parameter names already mapped into readings columns
- Modbus register decoding rules
- DB schema assumptions in `app/database/models.py`
- `/api/status` payload shape
- shared-bus validation logic

## How to safely add a new API endpoint

1. Add the route in `app/api/server.py`
2. Add business/data logic in `app/api/service.py`
3. If frontend uses it:
   - add client function in `frontend/src/api/energyApi.ts`
   - add/update type in `frontend/src/types/energy.ts`
   - wire through hooks/components as needed
4. Run:

```powershell
.\.venv\Scripts\python.exe -m compileall app main.py utils
cd frontend
npx tsc --noEmit
npm run build
```

## How to safely add a new meter parameter

1. Add the parameter to the correct parameter set in `config/meter_config.json`
2. Ensure the register/type/scale are correct
3. If decoding logic needs support, update `app/collectors/schneider/pm5000.py`
4. Confirm the generated DB column name is safe and unique
5. Restart backend so schema expansion runs
6. Verify new rows contain the value
7. Add frontend/report support only if needed

Critical warning:

- changing an existing parameter name changes the derived DB column name
- do not rename casually once pilot data exists

## How to safely add another meter template/driver

For a same-family meter with compatible registers:

- prefer adding a new parameter set/template in `config/meter_config.json`

For a truly different meter protocol/map:

- add a new collector file
- update `build_collector()` in `main.py`
- verify runtime meter-definition path

Do not pretend a new meter is supported unless the register map has been verified.

## How to safely change polling behavior

Files involved:

- `main.py`
- `app/services/polling_service.py`
- `app/collectors/modbus_client.py`
- `app/collectors/schneider/pm5000.py`
- `app/runtime_state.py`

After changing polling:

- verify backend imports
- verify compile
- verify one good meter still reads
- verify one bad meter does not break others
- verify `/api/status`

## How to safely change DB behavior

Files involved:

- `app/database/models.py`
- `app/database/repositories.py`

Rules:

- do not drop existing columns or tables casually
- do not change column derivation rules casually
- prefer additive changes

After DB changes:

- test startup schema creation
- test inserts
- test dashboard queries
- test export queries

## How to safely change frontend API assumptions

If a backend payload changes:

1. update frontend TypeScript types
2. update API wrapper functions
3. update affected pages/components
4. run:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

## Test checklist after common changes

### After polling changes

- backend starts
- one meter reads
- one bad meter fails safely
- `/api/status` updates

### After meter CRUD changes

- create meter
- edit meter
- disable meter
- dashboard selector still behaves

### After report/export changes

- Excel export
- Word export
- empty-range validation
- large-range validation

### After `/api/status` changes

- meter online/offline logic still makes sense
- stale logic still makes sense
- frontend still builds

## Release discipline recommendation

Before pushing significant changes:

1. commit locally with clear message
2. run backend compile/import checks
3. run frontend type/build checks
4. document behavior change if operators/developers will notice it
