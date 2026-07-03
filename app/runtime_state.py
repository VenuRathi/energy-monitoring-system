from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.collectors.modbus_client import ModbusRTUClient


_registry_lock = RLock()
_shared_modbus_clients: dict[tuple, "ModbusRTUClient"] = {}


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
