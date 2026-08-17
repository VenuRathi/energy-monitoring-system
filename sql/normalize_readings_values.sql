-- One-time cleanup for existing readings.
-- New readings are rounded by ReadingRepository before they are inserted.
-- This changes the existing readings columns in place.

DROP VIEW IF EXISTS meter_latest_readings;

DO $$
DECLARE
    column_record record;
BEGIN
    FOR column_record IN
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'readings'
          AND data_type IN ('double precision', 'numeric', 'real')
    LOOP
        EXECUTE format(
            'ALTER TABLE readings ALTER COLUMN %1$I TYPE NUMERIC(20,2) USING ROUND(%1$I::numeric, 2)',
            column_record.column_name
        );
    END LOOP;
END;
$$;
