# Boss Demo Script

This is a practical 10-15 minute demo flow for the current stabilized system.

## Before the demo

- Backend running
- Frontend running
- PostgreSQL running
- MTR-001 online
- MTR-002 online
- MTR-003 disabled
- `/api/status` healthy

## 1. Start backend

```powershell
.\.venv\Scripts\python.exe main.py
```

Point out:

- polling loop running
- no crash when meters fail individually
- runtime resilience and status tracking are active

## 2. Start frontend

```powershell
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## 3. Show dashboard

Explain:

- live meter selector
- latest readings
- trends
- dashboard no longer white-screens on missing/empty data

## 4. Show MTR-001 live data

Use the dashboard selector and show:

- recent values
- latest readings table
- trend chart

## 5. Show MTR-002 live data

Repeat with the second meter to prove multi-meter polling on one RS485 bus.

## 6. Open `/api/status`

Open:

```text
http://127.0.0.1:5000/api/status
```

Call out:

- API ok
- database ok
- polling running
- per-meter communication status
- latest successful reading timestamps
- stale meter count is zero

## 7. Explain online meters

Say clearly:

- `meter_id` is the software identifier
- `slave_id` is the physical Modbus address
- `MTR-001` and `MTR-002` are enabled and updating
- `MTR-003` is intentionally disabled because no physical meter is connected

## 8. Show PostgreSQL latest readings

Use `psql`:

```sql
SELECT DISTINCT ON (meter_id)
    meter_id,
    collected_at,
    active_power_total
FROM readings
ORDER BY meter_id, collected_at DESC;
```

Show that data is actually being stored, not just displayed in the UI.

## 9. Show Add / Configure Meter page

Explain:

- meter add/edit flow
- disable instead of destructive delete
- historical data is not removed when disabling a meter

## 10. Explain meter_id vs slave_id

Example:

- `MTR-001` -> internal software ID
- `slave_id=1` -> physical device address

## 11. Show disabled Meter 3 behavior

Demonstrate:

- `MTR-003` is visible as disabled
- it is not counted as stale
- it does not degrade live status

## 12. Show Excel export

Use a recent time range with data and export an `.xlsx` file.

Explain:

- date range validation exists
- empty or excessive ranges are handled more safely

## 13. Show Word report

Run the `.docx` export for the same meter/range.

## 14. Explain Phase 1, 2, and 3 improvements

### Phase 1

- dashboard no-crash behavior
- better empty states
- meter disable flow
- polling isolation

### Phase 2

- safer API URL handling
- API key mode
- CORS hardening
- debug safety

### Phase 3

- Modbus reconnect reliability
- retry amplification reduction
- per-meter runtime status
- polling heartbeat
- better database failure isolation

## 15. Remaining limitations

Be honest:

- API key is not full user authentication
- runtime status is in-memory and resets on restart
- polling is sequential
- retention/archiving is not automated yet
- browser-exposed `VITE_API_KEY` is only acceptable in a controlled environment

## 16. End with next steps for plant deployment

- controlled network deployment
- Windows service or watchdog
- retention/backup policy
- full authentication/authorization
- model-specific register map validation if additional meter types are added
