# PostgreSQL Verification Queries

Connect:

```powershell
psql -h localhost -U postgres -d energy_monitoring
```

## List all meters

```sql
SELECT meter_id, meter_name, location, enabled, com_port, slave_id
FROM meters
ORDER BY meter_id;
```

## List enabled meters

```sql
SELECT meter_id, meter_name, com_port, slave_id
FROM meters
WHERE enabled = TRUE
ORDER BY meter_id;
```

## List disabled meters

```sql
SELECT meter_id, meter_name, com_port, slave_id
FROM meters
WHERE enabled = FALSE
ORDER BY meter_id;
```

## Latest readings per meter

```sql
SELECT DISTINCT ON (meter_id)
    meter_id,
    timestamp,
    meter_timestamp,
    collected_at
FROM readings
ORDER BY meter_id, collected_at DESC;
```

## Row count per meter

```sql
SELECT meter_id, COUNT(*) AS reading_count
FROM readings
GROUP BY meter_id
ORDER BY meter_id;
```

## Readings in last 1 hour

```sql
SELECT meter_id, COUNT(*) AS rows_last_hour
FROM readings
WHERE collected_at >= NOW() - INTERVAL '1 hour'
GROUP BY meter_id
ORDER BY meter_id;
```

## Readings in last 24 hours

```sql
SELECT meter_id, COUNT(*) AS rows_last_24h
FROM readings
WHERE collected_at >= NOW() - INTERVAL '24 hours'
GROUP BY meter_id
ORDER BY meter_id;
```

## Check MTR-001 and MTR-002 are updating

```sql
SELECT DISTINCT ON (meter_id)
    meter_id,
    collected_at,
    timestamp,
    meter_timestamp
FROM readings
WHERE meter_id IN ('MTR-001', 'MTR-002')
ORDER BY meter_id, collected_at DESC;
```

## Check MTR-003 is disabled

```sql
SELECT meter_id, meter_name, enabled, com_port, slave_id
FROM meters
WHERE meter_id = 'MTR-003';
```

## Check latest timestamp and collected_at

```sql
SELECT
    meter_id,
    MAX(timestamp) AS latest_meter_time,
    MAX(collected_at) AS latest_collected_at
FROM readings
GROUP BY meter_id
ORDER BY meter_id;
```

## View latest common dashboard values

```sql
SELECT DISTINCT ON (meter_id)
    meter_id,
    collected_at,
    voltage_l_minus_n_avg,
    current_avg,
    active_power_total,
    frequency
FROM readings
ORDER BY meter_id, collected_at DESC;
```

## Basic database size check

```sql
SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size;
```

## Largest tables

```sql
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```
