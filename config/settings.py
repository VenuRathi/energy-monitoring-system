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
    app_timezone: str
    cors_allowed_origins: tuple[str, ...]
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
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
    allowed_origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173",
        ).split(",")
        if origin.strip()
    )

    return Settings(
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "18")),
        demo_mode=coerce_bool(os.getenv("DEMO_MODE", "false"), False),
        enable_database=enable_database,
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("API_PORT", "5000")),
        api_debug=coerce_bool(os.getenv("API_DEBUG", "false"), False),
        app_timezone=os.getenv("APP_TIMEZONE", "Asia/Calcutta"),
        cors_allowed_origins=allowed_origins or ("http://127.0.0.1:5173", "http://localhost:5173"),
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.getenv("DB_NAME", "energy_monitoring"),
        db_user=os.getenv("DB_USER", "postgres"),
        db_password=os.getenv("DB_PASSWORD", "postgres"),
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
