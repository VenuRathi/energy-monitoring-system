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
        self._failure_suppression_window_seconds = 30.0
        self._last_failure_signature: tuple[str, str, int, int, int, str] | None = None
        self._last_failure_logged_at = 0.0
        self._suppressed_failure_count = 0

    def _reset_client(self) -> None:
        if self._client is None:
            return
        try:
            self._client.close()
        except Exception:
            pass
        finally:
            self._client = None

    def _flush_suppressed_failures(self) -> None:
        if self._suppressed_failure_count <= 0 or self._last_failure_signature is None:
            return

        meter_id, port, slave_id, register, count, error_text = self._last_failure_signature
        logger.warning(
            "Suppressed %s repeated Modbus read failures for meter %s on %s slave %s register %s count %s: %s",
            self._suppressed_failure_count,
            meter_id or "unknown-meter",
            port,
            slave_id,
            register,
            count,
            error_text,
        )
        self._suppressed_failure_count = 0

    def _log_read_failure(
        self,
        *,
        meter_id: str | None,
        slave_id: int,
        register: int,
        count: int,
        error: str,
    ) -> None:
        now = time.monotonic()
        signature = (
            meter_id or "",
            self.port,
            slave_id,
            register,
            count,
            error,
        )

        if (
            signature == self._last_failure_signature
            and now - self._last_failure_logged_at < self._failure_suppression_window_seconds
        ):
            self._suppressed_failure_count += 1
            return

        self._flush_suppressed_failures()
        self._last_failure_signature = signature
        self._last_failure_logged_at = now
        logger.warning(
            "Modbus read failed for meter %s on %s slave %s register %s count %s: %s",
            meter_id or "unknown-meter",
            self.port,
            slave_id,
            register,
            count,
            error,
        )

    def connect(self) -> bool:
        with self._lock:
            if self._client and self._client.connected:
                return True
            if self._client and not self._client.connected:
                self._reset_client()

            now = time.monotonic()
            if now - self._last_connect_attempt_monotonic < self.reconnect_interval_seconds:
                return False
            self._last_connect_attempt_monotonic = now

            logger.info(
                "Attempting Modbus connection on %s with %s baud, parity %s, stop bits %s, byte size %s, timeout %.2fs.",
                self.port,
                self.baud_rate,
                self.parity,
                self.stop_bits,
                self.byte_size,
                self.timeout,
            )

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
                self._reset_client()
                logger.error(
                    "Unable to open Modbus port %s for slave %s: %s",
                    self.port,
                    self.slave_id,
                    exc,
                )
                return False

            if not connected:
                self._reset_client()
                logger.error(
                    "Unable to open Modbus port %s for slave %s.",
                    self.port,
                    self.slave_id,
                )
            return connected

    def close(self) -> None:
        with self._lock:
            self._reset_client()
            self._last_connect_attempt_monotonic = 0.0

    def read_holding_registers(
        self,
        register: int,
        count: int,
        one_based: bool = True,
        slave_id: Optional[int] = None,
        meter_id: str | None = None,
    ) -> Optional[list]:
        """
        Read holding registers.
        register: meter map register number (usually 1-based in datasheets).
        """
        with self._lock:
            resolved_slave_id = self.slave_id if slave_id is None else slave_id
            if not self.connect() or self._client is None:
                self._log_read_failure(
                    meter_id=meter_id,
                    slave_id=resolved_slave_id,
                    register=register,
                    count=count,
                    error="connection unavailable",
                )
                return None

            address = register - 1 if one_based else register
            try:
                response = self._client.read_holding_registers(
                    address=address,
                    count=count,
                    slave=resolved_slave_id,
                )
            except Exception as exc:
                self._reset_client()
                self._log_read_failure(
                    meter_id=meter_id,
                    slave_id=resolved_slave_id,
                    register=register,
                    count=count,
                    error=str(exc),
                )
                return None

            if response is None:
                self._reset_client()
                self._log_read_failure(
                    meter_id=meter_id,
                    slave_id=resolved_slave_id,
                    register=register,
                    count=count,
                    error="empty response",
                )
                return None

            if hasattr(response, "isError") and response.isError():
                self._reset_client()
                self._log_read_failure(
                    meter_id=meter_id,
                    slave_id=resolved_slave_id,
                    register=register,
                    count=count,
                    error=str(response),
                )
                return None

            if not hasattr(response, "registers") or len(response.registers) != count:
                actual_count = len(response.registers) if hasattr(response, "registers") else 0
                self._reset_client()
                self._log_read_failure(
                    meter_id=meter_id,
                    slave_id=resolved_slave_id,
                    register=register,
                    count=count,
                    error=f"incomplete register response ({actual_count}/{count})",
                )
                return None

            self._flush_suppressed_failures()
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
