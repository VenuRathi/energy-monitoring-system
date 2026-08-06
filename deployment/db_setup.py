from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql


def _add_repo_to_path(project_root: Path) -> None:
    sys.path.insert(0, str(project_root))


def _check(results: list[dict[str, Any]], status: str, label: str, detail: str) -> None:
    results.append(
        {
            "status": status,
            "label": label,
            "detail": detail,
        }
    )


def _meter_payload(meter: dict[str, Any]) -> dict[str, Any]:
    connection = dict(meter.get("connection") or {})
    return {
        "meter_id": meter["meter_id"],
        "meter_name": meter["meter_name"],
        "manufacturer": meter["manufacturer"],
        "model": meter["model"],
        "location": meter["location"],
        "protocol": meter["protocol"],
        "enabled": bool(meter.get("enabled", True)),
        "seu": bool(meter.get("seu", False)),
        "driver": meter.get("driver", "schneider.pm5000"),
        "com_port": connection.get("com_port") or connection.get("port", ""),
        "slave_id": int(connection.get("slave_id", 1)),
        "baud_rate": int(connection.get("baud_rate", 9600)),
        "parity": connection.get("parity", "N"),
        "stop_bits": int(connection.get("stop_bits", 1)),
        "byte_size": int(connection.get("byte_size", 8)),
        "timeout": float(connection.get("timeout", 2.0)),
        "one_based_map": bool(connection.get("one_based_map", True)),
    }


def _all_config_parameters(meter_config: dict[str, Any], parameter_name_to_column_name) -> list[dict[str, Any]]:
    unique_parameters: list[dict[str, Any]] = []
    seen_columns: set[str] = set()

    for meter in meter_config.get("meters", []):
        for parameter in meter.get("parameters", []):
            column_name = parameter_name_to_column_name(parameter["name"])
            if column_name in seen_columns:
                continue
            seen_columns.add(column_name)
            unique_parameters.append(parameter)

    return unique_parameters


def _database_exists(settings) -> bool:
    with psycopg.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname="postgres",
        user=settings.db_user,
        password=settings.db_password,
        connect_timeout=max(1, settings.db_connect_timeout_seconds),
        autocommit=True,
        application_name="energy_monitoring_deployment",
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (settings.db_name,))
            return cursor.fetchone() is not None


def _create_database(settings) -> None:
    with psycopg.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname="postgres",
        user=settings.db_user,
        password=settings.db_password,
        connect_timeout=max(1, settings.db_connect_timeout_seconds),
        autocommit=True,
        application_name="energy_monitoring_deployment",
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.db_name)))


def _verify_schema(connection, results: list[dict[str, Any]]) -> None:
    required_tables = [
        "meters",
        "readings",
        "alert_rules",
        "alert_events",
        "report_schedules",
        "email_settings",
        "runtime_settings",
        "hourly_readings",
    ]
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables
            WHERE table_schema = current_schema()
              AND table_name = ANY(%s);
            """,
            (required_tables,),
        )
        present_tables = {row[0] for row in cursor.fetchall()}
        for table_name in required_tables:
            if table_name in present_tables:
                _check(results, "PASS", f"{table_name} table", f"{table_name} exists")
            else:
                _check(results, "FAIL", f"{table_name} table", f"{table_name} is missing")

        if "readings" not in present_tables:
            _check(results, "FAIL", "readings schema details", "readings is missing; partition and recent-reading checks skipped")
            return

        cursor.execute(
            """
            SELECT COALESCE((
                SELECT c.relkind = 'p'
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = current_schema()
                  AND c.relname = 'readings'
            ), FALSE);
            """
        )
        readings_partitioned = bool(cursor.fetchone()[0])
        _check(
            results,
            "PASS" if readings_partitioned else "WARN",
            "readings partitioning",
            "readings is partitioned" if readings_partitioned else "readings is a plain table",
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM pg_inherits
            WHERE inhparent = 'readings'::regclass;
            """
        )
        partition_count = int(cursor.fetchone()[0])
        _check(results, "PASS" if partition_count > 0 else "WARN", "daily partitions", f"{partition_count} partition(s) found")

        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_views
                WHERE schemaname = current_schema()
                  AND viewname = 'meter_latest_readings'
            );
            """
        )
        has_latest_view = bool(cursor.fetchone()[0])
        _check(
            results,
            "PASS" if has_latest_view else "FAIL",
            "meter_latest_readings view",
            "view exists" if has_latest_view else "view is missing",
        )

        cursor.execute("SELECT COUNT(*) FROM meters;")
        meter_count = int(cursor.fetchone()[0])
        _check(results, "PASS" if meter_count > 0 else "WARN", "meters rows", f"{meter_count} meter row(s) in database")

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM readings
            WHERE timestamp >= now() - interval '24 hours';
            """
        )
        recent_readings = int(cursor.fetchone()[0])
        _check(
            results,
            "PASS" if recent_readings > 0 else "WARN",
            "recent readings",
            f"{recent_readings} reading row(s) in the last 24 hours",
        )


def run(project_root: Path, apply_schema: bool, create_database: bool, output_path: Path) -> int:
    _add_repo_to_path(project_root)
    os.chdir(project_root)

    from app.database.connection import get_connection
    from app.database.models import create_tables, parameter_name_to_column_name
    from app.database.repositories import MeterRepository
    from config.meter_loader import load_meter_config
    from config.settings import load_settings

    results: list[dict[str, Any]] = []
    settings = load_settings()
    meter_config = load_meter_config(str(project_root / "config" / "meter_config.json"))

    payload: dict[str, Any] = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "database": {
            "host": settings.db_host,
            "port": settings.db_port,
            "name": settings.db_name,
            "user": settings.db_user,
            "enable_database": settings.enable_database,
        },
        "checks": results,
    }

    try:
        if not _database_exists(settings):
            if create_database:
                _create_database(settings)
                _check(results, "PASS", "database exists", f"created database {settings.db_name}")
            else:
                _check(results, "FAIL", "database exists", f"database {settings.db_name} does not exist")
                output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                return 1
        else:
            _check(results, "PASS", "database exists", f"database {settings.db_name} exists")

        with get_connection(settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), now();")
                database_name, checked_at = cursor.fetchone()
            _check(results, "PASS", "database connection", f"connected to {database_name} at {checked_at}")

            if apply_schema:
                parameters = _all_config_parameters(meter_config, parameter_name_to_column_name)
                create_tables(connection, parameters, settings.poll_interval_seconds)
                repository = MeterRepository(connection)
                for meter in meter_config.get("meters", []):
                    repository.upsert_meter(_meter_payload(meter))
                _check(results, "PASS", "schema apply", "app schema and meter rows applied idempotently")
            else:
                _check(results, "PASS", "schema apply skipped", "read-only database verification requested")

            _verify_schema(connection, results)
    except Exception as exc:
        _check(results, "FAIL", "database setup", f"{type(exc).__name__}: {exc}")
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return 1

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0 if not any(check["status"] == "FAIL" for check in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Energy monitoring deployment database setup/check helper.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--outpu...t", required=True)
    parser.add_argument("--apply-schema", action="store_true")
    parser.add_argument("--create-database", action="store_true")
    args = parser.parse_args()

    return run(
        project_root=Path(args.project_root).resolve(),
        apply_schema=args.apply_schema,
        create_database=args.create_database,
        output_path=Path(args.output).resolve(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
