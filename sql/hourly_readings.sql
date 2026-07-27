-- Central PC hourly aggregate table for long-range dashboards and reports.
-- Run this after readings is present. Schedule refresh_hourly_readings(2)
-- every 5-15 minutes on the Central PC.

CREATE TABLE IF NOT EXISTS hourly_readings (
    hour_ts TIMESTAMPTZ NOT NULL,
    meter_id TEXT NOT NULL REFERENCES meters(meter_id),

    voltage_l_minus_n_avg_avg DOUBLE PRECISION,
    voltage_l_minus_n_avg_min DOUBLE PRECISION,
    voltage_l_minus_n_avg_max DOUBLE PRECISION,

    voltage_l_minus_l_avg_avg DOUBLE PRECISION,
    voltage_l_minus_l_avg_min DOUBLE PRECISION,
    voltage_l_minus_l_avg_max DOUBLE PRECISION,

    current_avg_avg DOUBLE PRECISION,
    current_avg_min DOUBLE PRECISION,
    current_avg_max DOUBLE PRECISION,

    active_power_total_avg DOUBLE PRECISION,
    active_power_total_min DOUBLE PRECISION,
    active_power_total_max DOUBLE PRECISION,

    reactive_power_total_avg DOUBLE PRECISION,
    reactive_power_total_min DOUBLE PRECISION,
    reactive_power_total_max DOUBLE PRECISION,

    apparent_power_total_avg DOUBLE PRECISION,
    apparent_power_total_min DOUBLE PRECISION,
    apparent_power_total_max DOUBLE PRECISION,

    frequency_avg DOUBLE PRECISION,
    frequency_min DOUBLE PRECISION,
    frequency_max DOUBLE PRECISION,

    power_factor_total_avg DOUBLE PRECISION,
    power_factor_total_min DOUBLE PRECISION,
    power_factor_total_max DOUBLE PRECISION,

    active_energy_received_out_of_load_min DOUBLE PRECISION,
    active_energy_received_out_of_load_max DOUBLE PRECISION,

    reactive_energy_received_min DOUBLE PRECISION,
    reactive_energy_received_max DOUBLE PRECISION,

    apparent_energy_received_min DOUBLE PRECISION,
    apparent_energy_received_max DOUBLE PRECISION,

    sample_count INTEGER NOT NULL,
    first_sample_ts TIMESTAMPTZ NOT NULL,
    last_sample_ts TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (hour_ts, meter_id)
);

CREATE INDEX IF NOT EXISTS idx_hourly_readings_meter_hour_desc
ON hourly_readings (meter_id, hour_ts DESC);

CREATE OR REPLACE FUNCTION refresh_hourly_readings(p_hours_back integer DEFAULT 2)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    affected_rows integer;
BEGIN
    INSERT INTO hourly_readings (
        hour_ts,
        meter_id,
        voltage_l_minus_n_avg_avg,
        voltage_l_minus_n_avg_min,
        voltage_l_minus_n_avg_max,
        voltage_l_minus_l_avg_avg,
        voltage_l_minus_l_avg_min,
        voltage_l_minus_l_avg_max,
        current_avg_avg,
        current_avg_min,
        current_avg_max,
        active_power_total_avg,
        active_power_total_min,
        active_power_total_max,
        reactive_power_total_avg,
        reactive_power_total_min,
        reactive_power_total_max,
        apparent_power_total_avg,
        apparent_power_total_min,
        apparent_power_total_max,
        frequency_avg,
        frequency_min,
        frequency_max,
        power_factor_total_avg,
        power_factor_total_min,
        power_factor_total_max,
        active_energy_received_out_of_load_min,
        active_energy_received_out_of_load_max,
        reactive_energy_received_min,
        reactive_energy_received_max,
        apparent_energy_received_min,
        apparent_energy_received_max,
        sample_count,
        first_sample_ts,
        last_sample_ts,
        updated_at
    )
    SELECT
        date_trunc('hour', timestamp) AS hour_ts,
        meter_id,
        AVG(voltage_l_minus_n_avg),
        MIN(voltage_l_minus_n_avg),
        MAX(voltage_l_minus_n_avg),
        AVG(voltage_l_minus_l_avg),
        MIN(voltage_l_minus_l_avg),
        MAX(voltage_l_minus_l_avg),
        AVG(current_avg),
        MIN(current_avg),
        MAX(current_avg),
        AVG(active_power_total),
        MIN(active_power_total),
        MAX(active_power_total),
        AVG(reactive_power_total),
        MIN(reactive_power_total),
        MAX(reactive_power_total),
        AVG(apparent_power_total),
        MIN(apparent_power_total),
        MAX(apparent_power_total),
        AVG(frequency),
        MIN(frequency),
        MAX(frequency),
        AVG(power_factor_total),
        MIN(power_factor_total),
        MAX(power_factor_total),
        MIN(active_energy_received_out_of_load),
        MAX(active_energy_received_out_of_load),
        MIN(reactive_energy_received),
        MAX(reactive_energy_received),
        MIN(apparent_energy_received),
        MAX(apparent_energy_received),
        COUNT(*),
        MIN(timestamp),
        MAX(timestamp),
        now()
    FROM readings
    WHERE timestamp >= date_trunc('hour', now()) - make_interval(hours => GREATEST(p_hours_back, 1))
    GROUP BY date_trunc('hour', timestamp), meter_id
    ON CONFLICT (hour_ts, meter_id)
    DO UPDATE SET
        voltage_l_minus_n_avg_avg = EXCLUDED.voltage_l_minus_n_avg_avg,
        voltage_l_minus_n_avg_min = EXCLUDED.voltage_l_minus_n_avg_min,
        voltage_l_minus_n_avg_max = EXCLUDED.voltage_l_minus_n_avg_max,
        voltage_l_minus_l_avg_avg = EXCLUDED.voltage_l_minus_l_avg_avg,
        voltage_l_minus_l_avg_min = EXCLUDED.voltage_l_minus_l_avg_min,
        voltage_l_minus_l_avg_max = EXCLUDED.voltage_l_minus_l_avg_max,
        current_avg_avg = EXCLUDED.current_avg_avg,
        current_avg_min = EXCLUDED.current_avg_min,
        current_avg_max = EXCLUDED.current_avg_max,
        active_power_total_avg = EXCLUDED.active_power_total_avg,
        active_power_total_min = EXCLUDED.active_power_total_min,
        active_power_total_max = EXCLUDED.active_power_total_max,
        reactive_power_total_avg = EXCLUDED.reactive_power_total_avg,
        reactive_power_total_min = EXCLUDED.reactive_power_total_min,
        reactive_power_total_max = EXCLUDED.reactive_power_total_max,
        apparent_power_total_avg = EXCLUDED.apparent_power_total_avg,
        apparent_power_total_min = EXCLUDED.apparent_power_total_min,
        apparent_power_total_max = EXCLUDED.apparent_power_total_max,
        frequency_avg = EXCLUDED.frequency_avg,
        frequency_min = EXCLUDED.frequency_min,
        frequency_max = EXCLUDED.frequency_max,
        power_factor_total_avg = EXCLUDED.power_factor_total_avg,
        power_factor_total_min = EXCLUDED.power_factor_total_min,
        power_factor_total_max = EXCLUDED.power_factor_total_max,
        active_energy_received_out_of_load_min = EXCLUDED.active_energy_received_out_of_load_min,
        active_energy_received_out_of_load_max = EXCLUDED.active_energy_received_out_of_load_max,
        reactive_energy_received_min = EXCLUDED.reactive_energy_received_min,
        reactive_energy_received_max = EXCLUDED.reactive_energy_received_max,
        apparent_energy_received_min = EXCLUDED.apparent_energy_received_min,
        apparent_energy_received_max = EXCLUDED.apparent_energy_received_max,
        sample_count = EXCLUDED.sample_count,
        first_sample_ts = EXCLUDED.first_sample_ts,
        last_sample_ts = EXCLUDED.last_sample_ts,
        updated_at = now();

    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RETURN affected_rows;
END;
$$;
