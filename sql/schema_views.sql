-- PostgreSQL views for monitoring dashboards and reporting
-- These views assume the expanded readings table created by app/database/models.py.

CREATE OR REPLACE VIEW meter_latest_readings AS
SELECT DISTINCT ON (r.meter_id)
    r.meter_id,
    m.meter_name,
    m.location,
    r.timestamp,
    r.current_avg,
    r.voltage_l_minus_n_avg,
    r.voltage_l_minus_l_avg,
    r.active_power_total,
    r.frequency,
    r.power_factor_total,
    r.active_energy_received_out_of_load,
    r.reactive_energy_received,
    r.apparent_energy_received,
    r.peak_demand
FROM readings r
JOIN meters m ON m.meter_id = r.meter_id
ORDER BY r.meter_id, r.timestamp DESC;
