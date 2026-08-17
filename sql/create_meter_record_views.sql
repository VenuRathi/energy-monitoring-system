-- Read-only convenience views for inspecting meter history in pgAdmin.
-- These views do not copy, delete, or modify readings.

CREATE OR REPLACE VIEW public.meter_records AS
SELECT
    r.*,
    m.meter_name,
    m.manufacturer,
    m.model,
    m.location,
    m.protocol,
    m.enabled AS meter_enabled,
    m.com_port,
    m.slave_id,
    m.baud_rate,
    m.parity,
    m.stop_bits,
    m.byte_size,
    m.timeout
FROM public.readings AS r
JOIN public.meters AS m USING (meter_id);

CREATE OR REPLACE VIEW public.readings_mtr1 AS
SELECT *
FROM public.meter_records
WHERE meter_id = 'MTR-001';

CREATE OR REPLACE VIEW public.readings_mtr2 AS
SELECT *
FROM public.meter_records
WHERE meter_id = 'MTR-002';
