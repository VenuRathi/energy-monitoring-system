import os
from dataclasses import dataclass

from dotenv import load_dotenv

from utils.coercion import coerce_bool


@dataclass
class Settings:
    poll_interval_seconds: int
    demo_mode: bool
    enable_database: bool
    api_host: str
    api_port: int
    api_debug: bool
    api_key_enabled: bool
    api_key: str
    app_timezone: str
    meter_clock_max_drift_seconds: int
    api_allowed_origins: tuple[str, ...]
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_connect_timeout_seconds: int
    readings_retention_days: int
    readings_cleanup_batch_size: int
    readings_cleanup_interval_hours: int
    reading_spool_path: str
    reading_spool_max_rows: int
    reading_spool_max_rows_per_meter: int
    reading_spool_retention_days: int
    reading_spool_replay_batch_size: int
    report_worker_enabled: bool
    report_worker_interval_seconds: int
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_use_tls: bool
    smtp_use_ssl: bool


def load_settings() -> Settings:
    load_dotenv()

    enable_database = coerce_bool(os.getenv("ENABLE_DATABASE", "false"), False)
    allowed_origins_value = os.getenv("API_ALLOWED_ORIGINS", os.getenv("CORS_ALLOWED_ORIGINS", ""))
    allowed_origins = tuple(
        origin.strip()
        for origin in allowed_origins_value.split(",")
        if origin.strip()
    )

    return Settings(
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "18")),
        demo_mode=coerce_bool(os.getenv("DEMO_MODE", "false"), False),
        enable_database=enable_database,
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("API_PORT", "5000")),
        api_debug=coerce_bool(os.getenv("API_DEBUG", "false"), False),
        api_key_enabled=coerce_bool(os.getenv("API_KEY_ENABLED", "false"), False),
        api_key=os.getenv("API_KEY", "").strip(),
        app_timezone=os.getenv("APP_TIMEZONE", "Asia/Calcutta"),
        meter_clock_max_drift_seconds=int(os.getenv("METER_CLOCK_MAX_DRIFT_SECONDS", "120")),
        api_allowed_origins=allowed_origins or ("http://127.0.0.1:5173", "http://localhost:5173"),
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.getenv("DB_NAME", "energy_monitoring"),
        db_user=os.getenv("DB_USER", "postgres"),
        db_password=os.getenv("DB_PASSWORD", "postgres"),
        db_connect_timeout_seconds=int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5")),
        readings_retention_days=int(os.getenv("READINGS_RETENTION_DAYS", "1825")),
        readings_cleanup_batch_size=int(os.getenv("READINGS_CLEANUP_BATCH_SIZE", "5000")),
        readings_cleanup_interval_hours=int(os.getenv("READINGS_CLEANUP_INTERVAL_HOURS", "1")),
        reading_spool_path=os.getenv("READING_SPOOL_PATH", "data/reading_spool.sqlite3"),
        reading_spool_max_rows=int(os.getenv("READING_SPOOL_MAX_ROWS", "100000")),
        reading_spool_max_rows_per_meter=int(os.getenv("READING_SPOOL_MAX_ROWS_PER_METER", "50000")),
        reading_spool_retention_days=int(os.getenv("READING_SPOOL_RETENTION_DAYS", "30")),
        reading_spool_replay_batch_size=int(os.getenv("READING_SPOOL_REPLAY_BATCH_SIZE", "500")),
        report_worker_enabled=coerce_bool(os.getenv("REPORT_WORKER_ENABLED", "true"), True),
        report_worker_interval_seconds=int(os.getenv("REPORT_WORKER_INTERVAL_SECONDS", "15")),
        smtp_host=os.getenv("SMTP_HOST", "").strip(),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", "").strip(),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_from_email=os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USERNAME", "")).strip(),
        smtp_use_tls=coerce_bool(os.getenv("SMTP_USE_TLS", "true"), True),
        smtp_use_ssl=coerce_bool(os.getenv("SMTP_USE_SSL", "false"), False),
    )


"""
## FILE EXPLANATION
Purpose:
This file loads all environment-based runtime settings.

Why this file exists:
Configuration must be centralized so business logic does not hardcode values.

What data enters the file:
Environment variables from .env and system environment.

What data leaves the file:
A Settings object used by service, database, and logging setup code.

Which layer of the architecture it belongs to:
Configuration Layer.

How it interacts with other files:
Used by main.py, database/connection.py usage flow, and services/polling_service.py
for runtime configuration values.
"""
