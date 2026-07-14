from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import TYPE_CHECKING, Iterable, Literal

if TYPE_CHECKING:
    from app.collectors.modbus_client import ModbusRTUClient


_registry_lock = RLock()
_shared_modbus_clients: dict[tuple, "ModbusRTUClient"] = {}
_meter_runtime_statuses: dict[str, dict] = {}
_polling_loop_state: dict[str, object] = {
    "startedAt": datetime.now(timezone.utc),
    "running": False,
    "cycleInProgress": False,
    "lastCycleStartTime": None,
    "lastCycleEndTime": None,
    "lastCycleDurationSeconds": None,
    "totalCyclesCompleted": 0,
    "lastGlobalPollingError": "",
    "lastGlobalPollingErrorTime": None,
}


def get_shared_modbus_client(client_key: tuple) -> "ModbusRTUClient | None":
    with _registry_lock:
        return _shared_modbus_clients.get(client_key)


def set_shared_modbus_client(client_key: tuple, modbus_client: "ModbusRTUClient") -> None:
    with _registry_lock:
        _shared_modbus_clients[client_key] = modbus_client


def pop_all_shared_modbus_clients() -> list["ModbusRTUClient"]:
    with _registry_lock:
        clients = list(_shared_modbus_clients.values())
        _shared_modbus_clients.clear()
        return clients


def _default_meter_runtime_status(meter_id: str) -> dict:
    return {
        "meterId": meter_id,
        "comPort": "",
        "slaveId": None,
        "lastPollAttemptTime": None,
        "lastSuccessfulReadingTime": None,
        "lastErrorTime": None,
        "lastErrorMessage": "",
        "consecutiveFailureCount": 0,
        "communicationStatus": "unknown",
    }


def ensure_meter_runtime_status(meter_id: str, *, com_port: str = "", slave_id: int | None = None) -> dict:
    with _registry_lock:
        state = _meter_runtime_statuses.setdefault(meter_id, _default_meter_runtime_status(meter_id))
        if com_port:
            state["comPort"] = com_port
        if slave_id is not None:
            state["slaveId"] = slave_id
        return deepcopy(state)


def prune_meter_runtime_statuses(active_meter_ids: Iterable[str]) -> None:
    allowed = set(active_meter_ids)
    with _registry_lock:
        for meter_id in list(_meter_runtime_statuses):
            if meter_id not in allowed:
                _meter_runtime_statuses.pop(meter_id, None)


def record_meter_poll_attempt(
    meter_id: str,
    *,
    attempted_at: datetime,
    com_port: str,
    slave_id: int | None,
) -> dict:
    with _registry_lock:
        state = _meter_runtime_statuses.setdefault(meter_id, _default_meter_runtime_status(meter_id))
        state["lastPollAttemptTime"] = attempted_at
        state["comPort"] = com_port
        state["slaveId"] = slave_id
        return deepcopy(state)


def record_meter_poll_success(
    meter_id: str,
    *,
    successful_at: datetime,
    communication_status: Literal["online", "warning"] = "online",
    com_port: str = "",
    slave_id: int | None = None,
    clear_error_message: bool = False,
) -> tuple[str, dict]:
    with _registry_lock:
        state = _meter_runtime_statuses.setdefault(meter_id, _default_meter_runtime_status(meter_id))
        previous_status = str(state.get("communicationStatus", "unknown"))
        state["lastSuccessfulReadingTime"] = successful_at
        state["consecutiveFailureCount"] = 0
        state["communicationStatus"] = communication_status
        if com_port:
            state["comPort"] = com_port
        if slave_id is not None:
            state["slaveId"] = slave_id
        if clear_error_message:
            state["lastErrorMessage"] = ""
        return previous_status, deepcopy(state)


def record_meter_poll_failure(
    meter_id: str,
    *,
    failed_at: datetime,
    error_message: str,
    com_port: str = "",
    slave_id: int | None = None,
) -> tuple[str, dict]:
    with _registry_lock:
        state = _meter_runtime_statuses.setdefault(meter_id, _default_meter_runtime_status(meter_id))
        previous_status = str(state.get("communicationStatus", "unknown"))
        state["lastErrorTime"] = failed_at
        state["lastErrorMessage"] = error_message
        state["consecutiveFailureCount"] = int(state.get("consecutiveFailureCount", 0)) + 1
        state["communicationStatus"] = "warning" if state["consecutiveFailureCount"] < 3 else "offline"
        if com_port:
            state["comPort"] = com_port
        if slave_id is not None:
            state["slaveId"] = slave_id
        return previous_status, deepcopy(state)


def record_meter_runtime_error(
    meter_id: str,
    *,
    error_at: datetime,
    error_message: str,
    com_port: str = "",
    slave_id: int | None = None,
    communication_status: Literal["unknown", "warning", "offline", "online"] | None = None,
) -> tuple[str, dict]:
    with _registry_lock:
        state = _meter_runtime_statuses.setdefault(meter_id, _default_meter_runtime_status(meter_id))
        previous_status = str(state.get("communicationStatus", "unknown"))
        state["lastErrorTime"] = error_at
        state["lastErrorMessage"] = error_message
        if communication_status is not None:
            state["communicationStatus"] = communication_status
        if com_port:
            state["comPort"] = com_port
        if slave_id is not None:
            state["slaveId"] = slave_id
        return previous_status, deepcopy(state)


def get_all_meter_runtime_statuses() -> dict[str, dict]:
    with _registry_lock:
        return deepcopy(_meter_runtime_statuses)


def set_polling_loop_running(running: bool) -> None:
    with _registry_lock:
        _polling_loop_state["running"] = running
        if not running:
            _polling_loop_state["cycleInProgress"] = False


def record_polling_cycle_start(started_at: datetime) -> dict:
    with _registry_lock:
        _polling_loop_state["running"] = True
        _polling_loop_state["cycleInProgress"] = True
        _polling_loop_state["lastCycleStartTime"] = started_at
        return deepcopy(_polling_loop_state)


def record_polling_cycle_end(ended_at: datetime, duration_seconds: float) -> dict:
    with _registry_lock:
        _polling_loop_state["running"] = True
        _polling_loop_state["cycleInProgress"] = False
        _polling_loop_state["lastCycleEndTime"] = ended_at
        _polling_loop_state["lastCycleDurationSeconds"] = duration_seconds
        _polling_loop_state["totalCyclesCompleted"] = int(_polling_loop_state["totalCyclesCompleted"]) + 1
        return deepcopy(_polling_loop_state)


def record_polling_loop_error(error_message: str, error_at: datetime) -> dict:
    with _registry_lock:
        _polling_loop_state["lastGlobalPollingError"] = error_message
        _polling_loop_state["lastGlobalPollingErrorTime"] = error_at
        return deepcopy(_polling_loop_state)


def get_polling_loop_state() -> dict:
    with _registry_lock:
        return deepcopy(_polling_loop_state)
