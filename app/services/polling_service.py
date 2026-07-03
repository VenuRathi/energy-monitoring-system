if __package__ is None or __package__ == "":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
import math
from datetime import datetime, timezone
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from app.collectors.base.base_meter import BaseMeter
from app.database.models import parameter_name_to_column_name
from app.database.repositories import AlertRuleRepository, MeterRepository, ReadingRepository


logger = logging.getLogger("energy_monitoring.polling_service")


class PollingService:
    def __init__(
        self,
        meter_config: dict,
        collector: BaseMeter,
        poll_interval_seconds: int,
        meter_repository: Optional[MeterRepository] = None,
        reading_repository: Optional[ReadingRepository] = None,
        alert_rule_repository: Optional[AlertRuleRepository] = None,
        app_timezone: str = "Asia/Calcutta",
    ) -> None:
        self.meter_config = meter_config
        self.collector = collector
        self.poll_interval_seconds = poll_interval_seconds
        self.meter_repository = meter_repository
        self.reading_repository = reading_repository
        self.alert_rule_repository = alert_rule_repository
        self.app_timezone = ZoneInfo(app_timezone)
        self.headers = ["Timestamp"] + [p["name"] + (f" ({p.get('unit')})" if p.get("unit") else "") for p in meter_config["parameters"]]
        self.parameter_lookup = {
            parameter_name_to_column_name(parameter["name"]): parameter for parameter in meter_config["parameters"]
        }

    def _meter_repository_payload(self) -> dict:
        connection = self.meter_config.get("connection", {})
        return {
            "meter_id": self.meter_config["meter_id"],
            "meter_name": self.meter_config["meter_name"],
            "manufacturer": self.meter_config["manufacturer"],
            "model": self.meter_config["model"],
            "location": self.meter_config["location"],
            "protocol": self.meter_config["protocol"],
            "enabled": self.meter_config.get("enabled", True),
            "seu": self.meter_config.get("seu", False),
            "driver": self.meter_config.get("driver", "schneider.pm5000"),
            "com_port": connection.get("com_port") or connection.get("port", ""),
            "slave_id": connection.get("slave_id", 1),
            "baud_rate": connection.get("baud_rate", 9600),
            "parity": connection.get("parity", "N"),
            "stop_bits": connection.get("stop_bits", 1),
            "byte_size": connection.get("byte_size", 8),
            "timeout": connection.get("timeout", 2.0),
            "one_based_map": connection.get("one_based_map", True),
        }

    def prepare(self) -> None:
        if self.meter_repository is not None:
            self.meter_repository.upsert_meter(self._meter_repository_payload())

    def poll_once(self) -> None:
        connection = self.meter_config.get("connection", {})
        logger.info(
            "Polling meter %s on %s slave %s.",
            self.meter_config["meter_id"],
            connection.get("com_port") or connection.get("port", "unknown-port"),
            connection.get("slave_id", "unknown-slave"),
        )
        collected_at = datetime.now(timezone.utc)
        readings = self.collector.read_all()
        meter_timestamp = self._resolve_meter_timestamp(readings, collected_at)
        reading_timestamp = meter_timestamp or collected_at
        reading_date = reading_timestamp.astimezone(self.app_timezone).strftime("%d/%m/%Y")
        reading_time = reading_timestamp.astimezone(self.app_timezone).strftime("%H:%M:%S")
        timestamp_source = "meter" if meter_timestamp is not None else "collector_fallback"

        non_null_count = sum(1 for value in readings.values() if value is not None)
        if non_null_count == 0:
            logger.warning("No readings received in this cycle for meter %s.", self.meter_config["meter_id"])
            return

        if not self._has_primary_measurements(readings):
            connection = self.meter_config.get("connection", {})
            logger.warning(
                "Meter %s on %s slave %s responded, but primary measurements are empty/zero. Persisting available values.",
                self.meter_config["meter_id"],
                connection.get("com_port") or connection.get("port", "unknown-port"),
                connection.get("slave_id", "unknown-slave"),
            )

        self._print_readings(reading_timestamp, collected_at, timestamp_source, readings)
        self._save_database(reading_timestamp, collected_at, reading_date, reading_time, timestamp_source, meter_timestamp, readings)
        self._evaluate_alerts(reading_timestamp, reading_date, reading_time, readings)
        logger.info("Finished polling meter %s.", self.meter_config["meter_id"])

    def _has_primary_measurements(self, readings: Dict[str, Optional[object]]) -> bool:
        keys_to_check = [
            "Voltage L-N Avg",
            "Voltage L-L Avg",
            "Current Avg",
            "Active Power Total",
            "Reactive Power Total",
            "Apparent Power Total",
            "Frequency",
        ]

        for key in keys_to_check:
            value = readings.get(key)
            if isinstance(value, (int, float)) and abs(float(value)) > 0.001:
                return True
        return False

    def _print_readings(
        self,
        reading_timestamp: datetime,
        collected_at: datetime,
        timestamp_source: str,
        readings: Dict[str, Optional[object]],
    ) -> None:
        logger.info("%s", "=" * 60)
        logger.info("Reading timestamp: %s [%s]", reading_timestamp.isoformat(), timestamp_source)
        logger.info("Collected at: %s", collected_at.isoformat())
        logger.info("%s", "=" * 60)

        for parameter in self.meter_config["parameters"]:
            name = parameter["name"]
            unit = parameter.get("unit", "")
            value = readings.get(name)

            if value is None:
                shown = "N/A"
            elif isinstance(value, float):
                shown = f"{value:.3f}"
            else:
                shown = str(value)

            if unit:
                logger.info("%-45s %12s %s", name, shown, unit)
            else:
                logger.info("%-45s %s", name, shown)

    def _save_database(
        self,
        reading_timestamp: datetime,
        collected_at: datetime,
        reading_date: str,
        reading_time: str,
        timestamp_source: str,
        meter_timestamp: datetime | None,
        readings: Dict[str, Optional[object]],
    ) -> None:
        if self.reading_repository is None:
            return

        self.reading_repository.insert_reading(
            meter_id=self.meter_config["meter_id"],
            timestamp=reading_timestamp,
            readings=readings,
            meter_timestamp=meter_timestamp,
            collected_at=collected_at,
            reading_date=reading_date,
            reading_time=reading_time,
            timestamp_source=timestamp_source,
        )

    def _resolve_meter_timestamp(self, readings: Dict[str, Optional[object]], collected_at: datetime) -> datetime | None:
        configured_name = str(self.meter_config.get("meter_timestamp_parameter", "")).strip()
        candidate_names: list[str] = []
        if configured_name:
            candidate_names.append(configured_name)

        for parameter in self.meter_config.get("parameters", []):
            if str(parameter.get("type", "")).lower() != "datetime4":
                continue
            normalized_name = str(parameter.get("name", "")).strip().lower()
            if normalized_name in {"meter date/time", "meter datetime", "meter clock", "date/time"}:
                candidate_names.append(parameter["name"])

        for candidate_name in candidate_names:
            decoded = self._decode_datetime4_raw(readings.get(candidate_name))
            if decoded is not None:
                return decoded

        detected_candidates: list[datetime] = []
        for parameter in self.meter_config.get("parameters", []):
            if str(parameter.get("type", "")).lower() != "datetime4":
                continue
            decoded = self._decode_datetime4_raw(readings.get(parameter["name"]))
            if decoded is None:
                continue
            age_seconds = abs((decoded.astimezone(timezone.utc) - collected_at).total_seconds())
            if age_seconds <= 48 * 3600:
                detected_candidates.append(decoded)

        if detected_candidates:
            return min(
                detected_candidates,
                key=lambda candidate: abs((candidate.astimezone(timezone.utc) - collected_at).total_seconds()),
            )
        return None

    def _decode_datetime4_raw(self, raw_value: object) -> datetime | None:
        if not isinstance(raw_value, str):
            return None

        pieces = raw_value.split("-")
        if len(pieces) != 4:
            return None

        try:
            words = [int(piece, 16) for piece in pieces]
        except ValueError:
            return None

        year = 2000 + (words[0] & 0x7F)
        day = words[1] & 0x1F
        month = (words[1] >> 8) & 0x0F
        minute = words[2] & 0x3F
        hour = (words[2] >> 8) & 0x1F
        millisecond = words[3] & 0xFFFF

        if millisecond > 59999:
            return None

        second = millisecond // 1000
        microsecond = (millisecond % 1000) * 1000

        try:
            return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=self.app_timezone)
        except ValueError:
            return None

    def _evaluate_alerts(
        self,
        reading_timestamp: datetime,
        reading_date: str,
        reading_time: str,
        readings: Dict[str, Optional[object]],
    ) -> None:
        if self.alert_rule_repository is None:
            return

        rules = self.alert_rule_repository.list_enabled_rules(self.meter_config["meter_id"])
        if not rules:
            return

        reading_by_key = {
            parameter_name_to_column_name(parameter["name"]): readings.get(parameter["name"])
            for parameter in self.meter_config["parameters"]
        }

        for rule in rules:
            value = reading_by_key.get(rule["parameter_key"])
            if not isinstance(value, (int, float)):
                continue

            numeric_value = float(value)
            if not math.isfinite(numeric_value):
                continue

            below_min = rule["min_value"] is not None and numeric_value < float(rule["min_value"])
            above_max = rule["max_value"] is not None and numeric_value > float(rule["max_value"])
            is_breached = below_min or above_max
            was_active = bool(rule.get("is_active"))
            parameter_label = self.parameter_lookup.get(rule["parameter_key"], {}).get("name", rule["parameter_key"])

            if is_breached and not was_active:
                self.alert_rule_repository.set_rule_state(
                    rule_id=rule["id"],
                    is_active=True,
                    last_value=numeric_value,
                    triggered_at=reading_timestamp,
                )
                self.alert_rule_repository.insert_event(
                    {
                        "rule_id": rule["id"],
                        "meter_id": self.meter_config["meter_id"],
                        "parameter_key": rule["parameter_key"],
                        "parameter_label": parameter_label,
                        "measured_value": numeric_value,
                        "min_value": rule["min_value"],
                        "max_value": rule["max_value"],
                        "event_type": "triggered",
                        "event_time": reading_timestamp,
                        "reading_date": reading_date,
                        "reading_time": reading_time,
                    }
                )
                continue

            if is_breached and was_active:
                self.alert_rule_repository.set_rule_state(
                    rule_id=rule["id"],
                    is_active=True,
                    last_value=numeric_value,
                )
                continue

            if not is_breached and was_active:
                self.alert_rule_repository.set_rule_state(
                    rule_id=rule["id"],
                    is_active=False,
                    last_value=numeric_value,
                    cleared_at=reading_timestamp,
                )
                self.alert_rule_repository.insert_event(
                    {
                        "rule_id": rule["id"],
                        "meter_id": self.meter_config["meter_id"],
                        "parameter_key": rule["parameter_key"],
                        "parameter_label": parameter_label,
                        "measured_value": numeric_value,
                        "min_value": rule["min_value"],
                        "max_value": rule["max_value"],
                        "event_type": "cleared",
                        "event_time": reading_timestamp,
                        "reading_date": reading_date,
                        "reading_time": reading_time,
                    }
                )


"""
## FILE EXPLANATION
Purpose:
This file runs periodic polling, prints results, and forwards selected values
to the database repository.

Why this file exists:
Business flow (polling cycles and data routing) belongs in service layer,
not in collector or database files.

What data enters the file:
Meter config, decoded readings from collector, and runtime settings.

What data leaves the file:
Console output and database reading inserts.

Which layer of the architecture it belongs to:
Service Layer.

How it interacts with other files:
It calls collector drivers for data, calls repositories for DB inserts, and is
instantiated by main.py with settings/config values.
"""
