import logging
import threading
import time
from typing import Optional

from pymodbus.client import ModbusSerialClient


logger = logging.getLogger("energy_monitoring.modbus_client")


class ModbusRTUClient:
    """Small wrapper around pymodbus client for RTU communication."""

    def __init__(
        self,
        port: str,
        baud_rate: int,
        parity: str,
        stop_bits: int,
        byte_size: int,
        slave_id: int,
        timeout: float = 2.0,
        reconnect_interval_seconds: float = 5.0,
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self.parity = parity
        self.stop_bits = stop_bits
        self.byte_size = byte_size
        self.slave_id = slave_id
        self.timeout = timeout
        self.reconnect_interval_seconds = reconnect_interval_seconds
        self._client: Optional[ModbusSerialClient] = None
        self._last_connect_attempt_monotonic = 0.0
        self._lock = threading.RLock()

    def connect(self) -> bool:
        with self._lock:
            if self._client and self._client.connected:
                return True

            now = time.monotonic()
            if now - self._last_connect_attempt_monotonic < self.reconnect_interval_seconds:
                return False
            self._last_connect_attempt_monotonic = now

            self._client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baud_rate,
                parity=self.parity,
                stopbits=self.stop_bits,
                bytesize=self.byte_size,
                timeout=self.timeout,
            )
            try:
                connected = bool(self._client.connect())
            except Exception as exc:
                logger.error(
                    "Unable to open Modbus port %s for slave %s: %s",
                    self.port,
                    self.slave_id,
                    exc,
                )
                return False

            if not connected:
                logger.error(
                    "Unable to open Modbus port %s for slave %s.",
                    self.port,
                    self.slave_id,
                )
            return connected

    def close(self) -> None:
        with self._lock:
            if self._client:
                self._client.close()
            self._last_connect_attempt_monotonic = 0.0

    def read_holding_registers(
        self,
        register: int,
        count: int,
        one_based: bool = True,
        slave_id: Optional[int] = None,
    ) -> Optional[list]:
        """
        Read holding registers.
        register: meter map register number (usually 1-based in datasheets).
        """
        with self._lock:
            if not self.connect() or self._client is None:
                logger.debug("Modbus connection unavailable for port %s.", self.port)
                return None

            address = register - 1 if one_based else register
            try:
                response = self._client.read_holding_registers(
                    address=address,
                    count=count,
                    slave=self.slave_id if slave_id is None else slave_id,
                )
            except Exception as exc:
                logger.warning(
                    "Modbus read failed on port %s (slave %s, register %s, count %s): %s",
                    self.port,
                    self.slave_id if slave_id is None else slave_id,
                    register,
                    count,
                    exc,
                )
                return None

            if response is None or (hasattr(response, "isError") and response.isError()):
                return None
            if not hasattr(response, "registers") or len(response.registers) != count:
                return None
            return response.registers


"""
## FILE EXPLANATION
Purpose:
This file handles low-level Modbus RTU read operations.

Why this file exists:
Driver files should focus on decoding parameters, not on connection and raw
register request details.

What data enters the file:
Serial settings, slave id, requested register number, and register count.

What data leaves the file:
A list of raw 16-bit register values, or None if read failed.

Which layer of the architecture it belongs to:
Collector Layer (protocol client helper).

How it interacts with other files:
Used by meter drivers such as schneider/pm5000.py. It is created in main.py
through service wiring.
"""
