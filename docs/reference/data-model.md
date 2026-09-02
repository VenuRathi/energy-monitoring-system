# Data Model Overview

This document summarizes the main persistence entities used by the backend.

## Core Tables

### meters
Purpose:
- Stores meter metadata and communication settings.

Key columns:
- `meter_id` (business key)
- `meter_name`, `location`, `manufacturer`, `model`
- `enabled`, `seu`, `driver`, `protocol`
- `com_port`, `slave_id`, `baud_rate`, `parity`, `stop_bits`, `byte_size`, `timeout`, `one_based_map`

### readings
Purpose:
- Stores timestamped meter measurements used by dashboard, trend, and reports.

Key columns:
- `meter_id` (FK-like relationship to `meters.meter_id`)
- `timestamp`, `meter_timestamp`, `collected_at`
- denormalized measurement columns (e.g., `active_power_total`, `current_avg`, etc.)

Operational rules:
- new installations create `readings` as a PostgreSQL range-partitioned table on `timestamp`
- production retention should drop old daily partitions instead of deleting rows
- exact duplicate inserts are enforced by PostgreSQL using `meter_id`, `timestamp`, and `timestamp_source`
- existing non-partitioned installations must run `sql/migrate_readings_to_daily_partitions.sql` after duplicate cleanup

Primary indexes:
- `(meter_id, timestamp DESC)` for latest readings and short trends
- `(meter_id, collected_at DESC)` for operational checks
- unique `(meter_id, timestamp, timestamp_source)` for duplicate protection

### hourly_readings
Purpose:
- Stores Central PC hourly aggregates for long-range dashboard and report queries.

Key columns:
- `hour_ts`, `meter_id`
- `*_avg`, `*_min`, and `*_max` columns for common dashboard measurements
- energy counter min/max columns for consumption calculations
- `sample_count`, `first_sample_ts`, `last_sample_ts`

Operational rules:
- create using `sql/hourly_readings.sql`
- refresh recent hours with `SELECT refresh_hourly_readings(2);`
- dashboards should use this table for long ranges instead of scanning raw `readings`

### alert_rules
Purpose:
- User-defined threshold rules per meter/parameter.

Key columns:
- `meter_id`, `parameter_key`
- `min_value`, `max_value`, `enabled`
- `is_active`, `last_value`, `last_triggered_at`, `last_cleared_at`

### report_schedules
Purpose:
- Scheduled report delivery configuration.

Key columns:
- `meter_id`, `meter_ids`
- `parameter_keys`
- `recipient_emails`
- `send_time`, `window_hours`, `enabled`

### email_settings
Purpose:
- SMTP configuration used by report/test email endpoints.

Key columns:
- `smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`
- `smtp_from_email`, `smtp_use_tls`, `smtp_use_ssl`

Production note:
- prefer setting `SMTP_PASSWORD` through environment or machine-level secret management
- when `SMTP_PASSWORD` is configured in the environment, it overrides the database password and UI saves do not store a new plaintext password

## Relationship Notes

- `meters` -> `readings`: one-to-many by `meter_id`.
- `meters` -> `alert_rules`: one-to-many by `meter_id`.
- `meters` -> `report_schedules`: one-to-many (primary meter), with support for multi-meter schedules through `meter_ids`.

## Operational Notes

- The schema is created/updated by backend startup (`create_tables`).
- Measurement columns are aligned with parameter keys generated from meter config names.
- Partitioned readings retention is configured with `READINGS_RETENTION_DAYS` and `READINGS_CLEANUP_INTERVAL_HOURS`.
- `READINGS_CLEANUP_BATCH_SIZE` is now only used by the pre-migration bounded-delete fallback.
