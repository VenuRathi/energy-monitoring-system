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

## Relationship Notes

- `meters` -> `readings`: one-to-many by `meter_id`.
- `meters` -> `alert_rules`: one-to-many by `meter_id`.
- `meters` -> `report_schedules`: one-to-many (primary meter), with support for multi-meter schedules through `meter_ids`.

## Operational Notes

- The schema is created/updated by backend startup (`ensure_schema`).
- Measurement columns are aligned with parameter keys generated from meter config names.
