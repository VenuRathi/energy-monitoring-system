-- Migration: convert the existing wide readings table to daily timestamp partitions.
--
-- Run only after a fresh PostgreSQL backup.
-- Stop the backend service before running this migration.
-- Check and resolve duplicates first:
--
-- SELECT meter_id, timestamp, timestamp_source, COUNT(*) AS duplicate_count
-- FROM readings
-- GROUP BY meter_id, timestamp, timestamp_source
-- HAVING COUNT(*) > 1
-- ORDER BY duplicate_count DESC, timestamp DESC;

BEGIN;

ALTER TABLE readings RENAME TO readings_legacy;

CREATE TABLE readings (
    LIKE readings_legacy INCLUDING DEFAULTS INCLUDING GENERATED INCLUDING IDENTITY
) PARTITION BY RANGE (timestamp);

ALTER TABLE readings
    ADD PRIMARY KEY (timestamp, id);

ALTER TABLE readings
    ADD UNIQUE (meter_id, timestamp, timestamp_source);

ALTER TABLE readings
    ADD CONSTRAINT readings_meter_id_fkey
    FOREIGN KEY (meter_id) REFERENCES meters(meter_id);

CREATE OR REPLACE FUNCTION ensure_daily_reading_partitions(
    p_days_back integer DEFAULT 1,
    p_days_ahead integer DEFAULT 7,
    p_partition_timezone text DEFAULT 'Asia/Calcutta'
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    d date;
    partition_name text;
    created_or_verified integer := 0;
BEGIN
    FOR d IN
        SELECT generate_series(
            current_date - p_days_back,
            current_date + p_days_ahead,
            interval '1 day'
        )::date
    LOOP
        partition_name := 'readings_' || to_char(d, 'YYYY_MM_DD');

        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF readings FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            d::timestamp AT TIME ZONE p_partition_timezone,
            (d + 1)::timestamp AT TIME ZONE p_partition_timezone
        );

        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (meter_id, timestamp DESC)',
            partition_name || '_meter_timestamp_idx',
            partition_name
        );

        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (meter_id, collected_at DESC)',
            partition_name || '_meter_collected_idx',
            partition_name
        );

        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (collected_at)',
            partition_name || '_collected_at_idx',
            partition_name
        );

        created_or_verified := created_or_verified + 1;
    END LOOP;

    RETURN created_or_verified;
END;
$$;

CREATE OR REPLACE FUNCTION drop_old_daily_reading_partitions(
    p_keep_days integer,
    p_dry_run boolean DEFAULT false
)
RETURNS TABLE(partition_name text, dropped boolean)
LANGUAGE plpgsql
AS $$
DECLARE
    cutoff_date date := current_date - p_keep_days;
    partition_date date;
    child record;
BEGIN
    IF p_keep_days <= 0 THEN
        RETURN;
    END IF;

    FOR child IN
        SELECT c.relname
        FROM pg_inherits i
        JOIN pg_class c ON c.oid = i.inhrelid
        JOIN pg_class p ON p.oid = i.inhparent
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE p.relname = 'readings'
          AND n.nspname = current_schema()
          AND c.relname ~ '^readings_[0-9]{4}_[0-9]{2}_[0-9]{2}$'
    LOOP
        partition_date := to_date(
            substring(child.relname from 'readings_([0-9]{4}_[0-9]{2}_[0-9]{2})'),
            'YYYY_MM_DD'
        );

        IF partition_date < cutoff_date THEN
            partition_name := child.relname;
            dropped := false;

            IF NOT p_dry_run THEN
                EXECUTE format('DROP TABLE IF EXISTS %I', child.relname);
                dropped := true;
            END IF;

            RETURN NEXT;
        END IF;
    END LOOP;
END;
$$;

WITH reading_bounds AS (
    SELECT
        COALESCE(MIN(timestamp)::date, current_date) AS oldest_day,
        COALESCE(MAX(timestamp)::date, current_date) AS newest_day
    FROM readings_legacy
)
SELECT ensure_daily_reading_partitions(
    GREATEST((current_date - oldest_day)::integer + 1, 1),
    GREATEST((newest_day - current_date)::integer + 7, 7)
)
FROM reading_bounds;

INSERT INTO readings
SELECT *
FROM readings_legacy
ON CONFLICT (meter_id, timestamp, timestamp_source) DO NOTHING;

CREATE SEQUENCE IF NOT EXISTS readings_id_seq;

SELECT setval(
    'readings_id_seq',
    (SELECT COALESCE(MAX(id), 0) + 1 FROM readings),
    false
);

ALTER TABLE readings
    ALTER COLUMN id SET DEFAULT nextval('readings_id_seq');

ALTER SEQUENCE readings_id_seq OWNED BY readings.id;

CREATE INDEX IF NOT EXISTS idx_readings_meter_timestamp_desc
ON readings (meter_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_readings_meter_collected_desc
ON readings (meter_id, collected_at DESC);

CREATE INDEX IF NOT EXISTS idx_readings_collected_at
ON readings (collected_at);

COMMIT;

-- Validate after commit:
--
-- SELECT COUNT(*) FROM readings_legacy;
-- SELECT COUNT(*) FROM readings;
--
-- SELECT inhrelid::regclass AS partition_name
-- FROM pg_inherits
-- WHERE inhparent = 'readings'::regclass
-- ORDER BY partition_name;
--
-- Keep readings_legacy for supervised validation, then drop it manually later:
-- DROP TABLE readings_legacy;
