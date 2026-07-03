import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from typing import Iterable
from werkzeug.serving import make_server

from app.api import app as api_app
from app.api.service import process_due_report_schedules
from config.meter_loader import load_meter_config
from config.settings import Settings, load_settings
from app.collectors.modbus_client import ModbusRTUClient
from app.collectors.schneider.pm5000 import PM5000Collector
from app.database.connection import get_connection
from app.database.models import create_tables
from app.database.repositories import AlertRuleRepository, MeterRepository, ReadingRepository
from app.runtime_state import get_shared_modbus_client as get_registered_modbus_client
from app.runtime_state import (
    pop_all_shared_modbus_clients,
    prune_meter_runtime_statuses,
    record_meter_runtime_error,
    record_polling_cycle_end,
    record_polling_cycle_start,
    record_polling_loop_error,
    set_polling_loop_running,
    set_shared_modbus_client,
)
from app.services.polling_service import PollingService
from utils.coercion import coerce_bool
from utils.logger import setup_logger

try:
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows fallback
    msvcrt = None

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows path
    fcntl = None


_INSTANCE_LOCK_HANDLE = None
_INSTANCE_LOCK_PATH = Path(tempfile.gettempdir()) / "energy-monitoring-system-main.lock"


class SingleInstanceError(RuntimeError):
    """Raised when another main.py process is already running."""


def acquire_instance_lock() -> None:
    global _INSTANCE_LOCK_HANDLE

    if _INSTANCE_LOCK_HANDLE is not None:
        return

    _INSTANCE_LOCK_PATH.touch(exist_ok=True)
    lock_handle = _INSTANCE_LOCK_PATH.open("r+", encoding="utf-8")
    try:
        if _INSTANCE_LOCK_PATH.stat().st_size == 0:
            lock_handle.seek(0)
            lock_handle.write("0")
            lock_handle.flush()

        if os.name == "nt" and msvcrt is not None:
            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
        elif fcntl is not None:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:  # pragma: no cover - unsupported platform fallback
            raise RuntimeError("Single-instance lock is not supported on this platform.")
    except OSError as exc:
        lock_handle.close()
        raise SingleInstanceError(
            "Another energy monitoring service instance is already running. "
            "Stop the existing process before starting a new one."
        ) from exc

    lock_handle.seek(0)
    lock_handle.truncate()
    lock_handle.write(str(os.getpid()))
    lock_handle.flush()
    _INSTANCE_LOCK_HANDLE = lock_handle


def release_instance_lock() -> None:
    global _INSTANCE_LOCK_HANDLE

    if _INSTANCE_LOCK_HANDLE is None:
        return

    try:
        if os.name == "nt" and msvcrt is not None:
            _INSTANCE_LOCK_HANDLE.seek(0)
            msvcrt.locking(_INSTANCE_LOCK_HANDLE.fileno(), msvcrt.LK_UNLCK, 1)
        elif fcntl is not None:
            fcntl.flock(_INSTANCE_LOCK_HANDLE.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    finally:
        _INSTANCE_LOCK_HANDLE.close()
        _INSTANCE_LOCK_HANDLE = None


class EmbeddedApiServer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger("energy_monitoring.api")
        self._server = make_server(
            settings.api_host,
            settings.api_port,
            api_app,
            threaded=True,
        )
        self._thread = Thread(target=self._server.serve_forever, name="embedded-flask-api", daemon=True)

    def start(self) -> None:
        self._thread.start()
        self.logger.info(
            "Embedded Flask API started on http://%s:%s within PID %s",
            self.settings.api_host,
            self.settings.api_port,
            os.getpid(),
        )

    def stop(self) -> None:
        try:
            self._server.shutdown()
        except Exception as exc:
            self.logger.exception("Embedded API shutdown failed: %s", exc)


def start_embedded_api(settings: Settings) -> EmbeddedApiServer:
    logger = logging.getLogger("energy_monitoring.api")
    try:
        server = EmbeddedApiServer(settings)
        server.start()
        return server
    except Exception as exc:
        logger.exception("Embedded API server failed: %s", exc)
        raise


def build_modbus_client(connection_config: dict) -> ModbusRTUClient:
    return ModbusRTUClient(
        port=connection_config.get("com_port") or connection_config.get("port", "COM6"),
        baud_rate=int(connection_config.get("baud_rate", 9600)),
        parity=connection_config.get("parity", "N"),
        stop_bits=int(connection_config.get("stop_bits", 1)),
        byte_size=int(connection_config.get("byte_size", 8)),
        slave_id=int(connection_config.get("slave_id", 1)),
        timeout=float(connection_config.get("timeout", 2.0)),
    )


def modbus_client_key(connection_config: dict) -> tuple:
    return (
        connection_config.get("com_port") or connection_config.get("port", "COM6"),
        int(connection_config.get("baud_rate", 9600)),
        connection_config.get("parity", "N"),
        int(connection_config.get("stop_bits", 1)),
        int(connection_config.get("byte_size", 8)),
        float(connection_config.get("timeout", 2.0)),
    )


def build_collector(meter_definition: dict, modbus_client: ModbusRTUClient):
    driver_name = meter_definition.get("driver", "schneider.pm5000")
    connection_config = meter_definition.get("connection", {})

    if driver_name == "schneider.pm5000":
        return PM5000Collector(
            modbus_client=modbus_client,
            parameters=meter_definition["parameters"],
            slave_id=int(connection_config.get("slave_id", 1)),
            meter_id=meter_definition["meter_id"],
            one_based_map=connection_config.get("one_based_map", True),
        )

    raise ValueError(f"Unsupported meter driver '{driver_name}' for meter '{meter_definition['meter_id']}'.")


def _meter_templates_by_id(meter_config: dict) -> dict[str, dict]:
    return {meter["meter_id"]: meter for meter in meter_config.get("meters", [])}


def _template_for_driver(driver_name: str, meter_config: dict) -> dict:
    for meter in meter_config.get("meters", []):
        if meter.get("driver") == driver_name:
            return meter
    raise ValueError(
        f"No parameter template is configured for driver '{driver_name}' in config/meter_config.json."
    )


def _connection_config_from_meter(db_meter: dict, default_connection: dict) -> dict:
    return {
        "com_port": db_meter.get("com_port") or db_meter.get("port") or default_connection.get("port", "COM6"),
        "port": db_meter.get("com_port") or db_meter.get("port") or default_connection.get("port", "COM6"),
        "slave_id": int(db_meter.get("slave_id", default_connection.get("slave_id", 1))),
        "baud_rate": int(db_meter.get("baud_rate", default_connection.get("baud_rate", 9600))),
        "parity": db_meter.get("parity", default_connection.get("parity", "N")),
        "stop_bits": int(db_meter.get("stop_bits", default_connection.get("stop_bits", 1))),
        "byte_size": int(db_meter.get("byte_size", default_connection.get("byte_size", 8))),
        "timeout": float(db_meter.get("timeout", default_connection.get("timeout", 2.0))),
        "one_based_map": coerce_bool(db_meter.get("one_based_map", default_connection.get("one_based_map", True)), True),
    }


def build_runtime_meter_definition(db_meter: dict, meter_config: dict) -> dict:
    templates = _meter_templates_by_id(meter_config)
    driver_name = db_meter.get("driver", meter_config.get("meter_defaults", {}).get("driver", "schneider.pm5000"))
    template = templates.get(db_meter["meter_id"]) or _template_for_driver(driver_name, meter_config)
    connection_config = dict(template.get("connection", {}))
    connection_config.update(_connection_config_from_meter(db_meter, connection_config))

    meter_definition = dict(template)
    meter_definition.update(
        {
            "meter_id": db_meter["meter_id"],
            "meter_name": db_meter.get("meter_name", template.get("meter_name", db_meter["meter_id"])),
            "location": db_meter.get("location", template.get("location", "")),
            "enabled": coerce_bool(db_meter.get("enabled", True), True),
            "seu": coerce_bool(db_meter.get("seu", template.get("seu", False)), False),
            "driver": db_meter.get("driver", template.get("driver", "schneider.pm5000")),
            "com_port": connection_config["com_port"],
            "slave_id": connection_config["slave_id"],
            "baud_rate": connection_config["baud_rate"],
            "parity": connection_config["parity"],
            "stop_bits": connection_config["stop_bits"],
            "byte_size": connection_config["byte_size"],
            "timeout": connection_config["timeout"],
            "one_based_map": connection_config["one_based_map"],
            "connection": connection_config,
        }
    )
    return meter_definition


def load_runtime_meters(settings, meter_config: dict) -> list[dict]:
    if not settings.enable_database:
        return [meter for meter in meter_config.get("meters", []) if coerce_bool(meter.get("enabled", True), True)]

    connection = get_connection(settings)
    try:
        repository = MeterRepository(connection)
        db_meters = repository.list_meters()
        if not db_meters:
            return [meter for meter in meter_config.get("meters", []) if coerce_bool(meter.get("enabled", True), True)]
        return [build_runtime_meter_definition(meter, meter_config) for meter in db_meters if coerce_bool(meter.get("enabled", True), True)]
    finally:
        connection.close()


def _meter_signature(meter_definition: dict) -> tuple:
    connection = meter_definition.get("connection", {})
    parameter_keys = tuple(parameter.get("name", "") for parameter in meter_definition.get("parameters", []))
    return (
        meter_definition.get("meter_id", ""),
        meter_definition.get("meter_name", ""),
        meter_definition.get("location", ""),
        meter_definition.get("manufacturer", ""),
        meter_definition.get("model", ""),
        meter_definition.get("protocol", ""),
        coerce_bool(meter_definition.get("enabled", True), True),
        coerce_bool(meter_definition.get("seu", False), False),
        meter_definition.get("driver", ""),
        connection.get("port") or connection.get("com_port", ""),
        int(connection.get("slave_id", 1)),
        int(connection.get("baud_rate", 9600)),
        connection.get("parity", "N"),
        int(connection.get("stop_bits", 1)),
        int(connection.get("byte_size", 8)),
        float(connection.get("timeout", 2.0)),
        coerce_bool(connection.get("one_based_map", True), True),
        parameter_keys,
    )


def _meter_set_signature(meter_definitions: Iterable[dict]) -> tuple:
    return tuple(sorted(_meter_signature(meter_definition) for meter_definition in meter_definitions))


def _close_modbus_clients(shared_modbus_clients: dict[tuple, ModbusRTUClient]) -> None:
    for modbus_client in shared_modbus_clients.values():
        modbus_client.close()
    shared_modbus_clients.clear()
    for modbus_client in pop_all_shared_modbus_clients():
        try:
            modbus_client.close()
        except Exception:
            pass


def _validate_shared_bus_settings(meter_definitions: list[dict], logger: logging.Logger) -> list[dict]:
    valid_meter_definitions: list[dict] = []
    serial_settings_by_port: dict[str, tuple[int, str, int, int, float]] = {}

    for meter_definition in meter_definitions:
        connection = meter_definition.get("connection", {})
        meter_id = meter_definition.get("meter_id", "unknown-meter")
        com_port = str(connection.get("com_port") or connection.get("port", "unknown-port")).upper()
        slave_id = connection.get("slave_id", "unknown-slave")
        serial_settings = (
            int(connection.get("baud_rate", 9600)),
            str(connection.get("parity", "N")),
            int(connection.get("stop_bits", 1)),
            int(connection.get("byte_size", 8)),
            float(connection.get("timeout", 2.0)),
        )
        existing_settings = serial_settings_by_port.get(com_port)
        if existing_settings is not None and existing_settings != serial_settings:
            message = (
                f"Skipping meter {meter_id} on {com_port} slave {slave_id}: "
                f"serial settings {serial_settings} conflict with existing bus settings {existing_settings}."
            )
            logger.warning(message)
            record_meter_runtime_error(
                meter_id,
                error_at=datetime.now(timezone.utc),
                error_message=message,
                com_port=com_port,
                slave_id=int(slave_id) if isinstance(slave_id, int) else None,
                communication_status="warning",
            )
            continue

        serial_settings_by_port[com_port] = serial_settings
        valid_meter_definitions.append(meter_definition)

    return valid_meter_definitions


def build_polling_service(
    meter_definition: dict,
    settings,
    meter_repository: MeterRepository | None,
    modbus_client: ModbusRTUClient,
) -> PollingService:
    collector = build_collector(meter_definition, modbus_client)
    scoped_reading_repository = None
    if settings.enable_database:
        scoped_reading_repository = ReadingRepository(
            connection=None,
            parameters=meter_definition["parameters"],
            settings=settings,
        )
    alert_rule_repository = AlertRuleRepository(connection=None, settings=settings) if settings.enable_database else None

    return PollingService(
        meter_config=meter_definition,
        collector=collector,
        poll_interval_seconds=settings.poll_interval_seconds,
        meter_repository=meter_repository,
        reading_repository=scoped_reading_repository,
        alert_rule_repository=alert_rule_repository,
        app_timezone=settings.app_timezone,
    )


def main() -> None:
    logger = setup_logger()
    acquire_instance_lock()
    settings = load_settings()
    meter_config = load_meter_config()
    api_server = start_embedded_api(settings)
    meter_definitions = load_runtime_meters(settings, meter_config)
    logger.info("Starting energy monitoring with %s enabled meter(s).", len(meter_definitions))

    # Database setup (optional)
    meter_repository = None
    if settings.enable_database:
        all_parameters = []
        for meter in meter_config.get("meters", []):
            all_parameters.extend(meter.get("parameters", []))
        with get_connection(settings) as connection:
            create_tables(connection, all_parameters)
        meter_repository = MeterRepository(connection=None, settings=settings)
        logger.info("PostgreSQL logging is enabled.")
    else:
        logger.info("PostgreSQL logging is disabled.")

    shared_modbus_clients: dict[tuple, ModbusRTUClient] = {}

    def get_shared_modbus_client(meter_definition: dict) -> ModbusRTUClient:
        connection_config = meter_definition.get("connection", {})
        client_key = modbus_client_key(connection_config)
        modbus_client = shared_modbus_clients.get(client_key) or get_registered_modbus_client(client_key)
        if modbus_client is None:
            modbus_client = build_modbus_client(connection_config)
            shared_modbus_clients[client_key] = modbus_client
            set_shared_modbus_client(client_key, modbus_client)
        return modbus_client

    polling_services: list[PollingService] = []
    active_signature: tuple = ()

    def rebuild_polling_services(next_meter_definitions: list[dict]) -> None:
        nonlocal polling_services, active_signature
        _close_modbus_clients(shared_modbus_clients)
        next_polling_services: list[PollingService] = []
        for meter_definition in next_meter_definitions:
            connection = meter_definition.get("connection", {})
            meter_id = meter_definition.get("meter_id", "unknown-meter")
            com_port = connection.get("com_port") or connection.get("port", "unknown-port")
            slave_id = connection.get("slave_id", "unknown-slave")
            try:
                polling_service = build_polling_service(
                    meter_definition=meter_definition,
                    settings=settings,
                    meter_repository=meter_repository,
                    modbus_client=get_shared_modbus_client(meter_definition),
                )
                polling_service.prepare()
                next_polling_services.append(polling_service)
            except Exception as exc:
                logger.exception(
                    "Skipping meter %s on %s slave %s during polling service rebuild: %s",
                    meter_id,
                    com_port,
                    slave_id,
                    exc,
                )
                record_meter_runtime_error(
                    meter_id,
                    error_at=datetime.now(timezone.utc),
                    error_message=f"Polling service rebuild failed: {exc}",
                    com_port=str(com_port),
                    slave_id=int(slave_id) if isinstance(slave_id, int) else None,
                    communication_status="warning",
                )
        polling_services = next_polling_services
        prune_meter_runtime_statuses(
            meter_definition.get("meter_id", "")
            for meter_definition in next_meter_definitions
            if meter_definition.get("meter_id")
        )
        active_signature = _meter_set_signature(next_meter_definitions)
        logger.info("Active polling meters refreshed: %s meter(s).", len(polling_services))

    def sync_polling_services() -> None:
        nonlocal meter_definitions
        try:
            next_meter_definitions = load_runtime_meters(settings, meter_config)
        except Exception as exc:
            record_polling_loop_error(f"Failed to refresh runtime meter definitions: {exc}", datetime.now(timezone.utc))
            logger.exception("Failed to refresh runtime meter definitions: %s", exc)
            return

        validated_meter_definitions = _validate_shared_bus_settings(next_meter_definitions, logger)
        next_signature = _meter_set_signature(validated_meter_definitions)
        if next_signature == active_signature:
            return

        meter_definitions = validated_meter_definitions
        rebuild_polling_services(validated_meter_definitions)

    try:
        sync_polling_services()
        set_polling_loop_running(True)

        while True:
            cycle_started_at = datetime.now(timezone.utc)
            cycle_started_monotonic = time.monotonic()
            record_polling_cycle_start(cycle_started_at)
            logger.info("Polling cycle started at %s.", cycle_started_at.isoformat())
            sync_polling_services()
            if not polling_services:
                logger.warning("No enabled meters are active for polling.")
                cycle_ended_at = datetime.now(timezone.utc)
                cycle_duration_seconds = time.monotonic() - cycle_started_monotonic
                record_polling_cycle_end(cycle_ended_at, cycle_duration_seconds)
                logger.info(
                    "Polling cycle ended at %s after %.3fs with no active meters.",
                    cycle_ended_at.isoformat(),
                    cycle_duration_seconds,
                )
                time.sleep(settings.poll_interval_seconds)
                continue
            for polling_service in polling_services:
                connection = polling_service.meter_config.get("connection", {})
                meter_id = polling_service.meter_config.get("meter_id", "unknown-meter")
                com_port = connection.get("com_port") or connection.get("port", "unknown-port")
                slave_id = connection.get("slave_id", "unknown-slave")
                try:
                    polling_service.poll_once()
                except Exception as exc:
                    record_polling_loop_error(f"Meter polling failure for {meter_id}: {exc}", datetime.now(timezone.utc))
                    logger.exception(
                        "Polling failed for meter %s on %s slave %s: %s",
                        meter_id,
                        com_port,
                        slave_id,
                        exc,
                    )
            try:
                process_due_report_schedules()
            except Exception as exc:
                record_polling_loop_error(f"Scheduled report processing failed: {exc}", datetime.now(timezone.utc))
                logger.exception("Scheduled report processing failed: %s", exc)
            cycle_ended_at = datetime.now(timezone.utc)
            cycle_duration_seconds = time.monotonic() - cycle_started_monotonic
            record_polling_cycle_end(cycle_ended_at, cycle_duration_seconds)
            logger.info(
                "Polling cycle ended at %s after %.3fs across %s meter(s).",
                cycle_ended_at.isoformat(),
                cycle_duration_seconds,
                len(polling_services),
            )
            time.sleep(settings.poll_interval_seconds)
    finally:
        set_polling_loop_running(False)
        api_server.stop()
        _close_modbus_clients(shared_modbus_clients)
        release_instance_lock()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.getLogger("energy_monitoring.main").info("Program stopped manually.")
    except SingleInstanceError as exc:
        logging.getLogger("energy_monitoring.main").error("%s", exc)
    except Exception as e:
        logging.getLogger("energy_monitoring.main").exception("Unhandled error: %s", e)
        raise
