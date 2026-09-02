if __package__ is None or __package__ == "":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import math
import struct
from typing import Dict, List, Optional

from app.collectors.base.base_meter import BaseMeter
from app.collectors.modbus_client import ModbusRTUClient

MAX_BLOCK_WORDS = 16
MAX_GAP_WORDS = 2


class PM5000Collector(BaseMeter):
    """Collector for Schneider PM5000 / EM6400 style register map."""

    def __init__(
        self,
        modbus_client: ModbusRTUClient,
        parameters: List[dict],
        slave_id: int,
        meter_id: str,
        one_based_map: bool = True,
    ) -> None:
        self.modbus_client = modbus_client
        self.parameters = parameters
        self.slave_id = slave_id
        self.meter_id = meter_id
        self.one_based_map = one_based_map

    def read_all(self) -> Dict[str, Optional[object]]:
        register_state = self._prefetch_register_blocks()
        readings: Dict[str, Optional[object]] = {}
        if register_state["communication_failed"]:
            for parameter in self.parameters:
                readings[parameter["name"]] = None
            return readings
        for parameter in self.parameters:
            name = parameter["name"]
            readings[name] = self._read_parameter(parameter, register_state)
        return readings

    def _read_parameter(
        self,
        parameter: dict,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[object]:
        register = int(parameter["register"])
        data_type = str(parameter["type"]).lower()
        scale = float(parameter.get("scale", 1.0))

        if data_type == "float32":
            raw_value = self._read_float32(register, register_state)
        elif data_type == "int32":
            raw_value = self._read_int32_lsw(register, register_state)
        elif data_type == "int64":
            raw_value = self._read_int64_lsw(register, register_state)
        elif data_type == "uint64":
            raw_value = self._read_uint64(register, register_state)
        elif data_type == "uint16":
            raw_value = self._read_uint16(register, register_state)
        elif data_type == "datetime4":
            # Keep vendor datetime as raw register string until exact format is specified.
            return self._read_datetime4_raw(register, register_state)
        else:
            raw_value = self._read_uint32_lsw(register, register_state)

        if raw_value is None:
            return None

        value = raw_value * scale
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return self._sanitize_value(parameter, value)

    def _sanitize_value(self, parameter: dict, value: object) -> Optional[object]:
        if value is None or not isinstance(value, (int, float)):
            return value

        numeric = float(value)
        if not math.isfinite(numeric):
            return None

        name = str(parameter.get("name", "")).lower()
        unit = str(parameter.get("unit", "")).lower()

        if "frequency" in name and not (40.0 <= numeric <= 70.0):
            return None
        if unit == "pf" and abs(numeric) > 1.2:
            return None
        if unit == "%" and (numeric < 0 or numeric > 100):
            return None
        if name.startswith("voltage") and numeric < 0:
            return None
        if name.startswith("current") and numeric < 0:
            return None
        if "demand" in name and "datetime" not in name and numeric < 0:
            return None

        return value

    def _word_count_for_type(self, data_type: str) -> int:
        if data_type == "datetime4":
            return 4
        if data_type == "int64":
            return 4
        if data_type == "uint16":
            return 1
        if data_type == "uint64":
            return 4
        return 2

    def _build_read_plan(self) -> list[tuple[int, int]]:
        spans = sorted(
            (
                int(parameter["register"]),
                self._word_count_for_type(str(parameter["type"]).lower()),
            )
            for parameter in self.parameters
        )
        if not spans:
            return []

        plan: list[tuple[int, int]] = []
        start, count = spans[0]
        end = start + count

        for next_start, next_count in spans[1:]:
            next_end = next_start + next_count
            gap = next_start - end
            projected_count = next_end - start
            if gap <= MAX_GAP_WORDS and projected_count <= MAX_BLOCK_WORDS:
                end = max(end, next_end)
                continue

            plan.append((start, end - start))
            start = next_start
            end = next_end

        plan.append((start, end - start))
        return plan

    def _prefetch_register_blocks(self) -> dict[str, object]:
        blocks: list[tuple[int, list[int]]] = []
        failed_optional_blocks: list[tuple[int, int]] = []
        for register, count in self._build_read_plan():
            regs = self.modbus_client.read_holding_registers(
                register,
                count=count,
                one_based=self.one_based_map,
                slave_id=self.slave_id,
                meter_id=self.meter_id,
            )
            if regs is None:
                if self._is_optional_datetime_block(register, count):
                    failed_optional_blocks.append((register, register + count))
                    continue
                return {
                    "blocks": blocks,
                    "failed_optional_blocks": failed_optional_blocks,
                    "communication_failed": True,
                }
            blocks.append((register, regs))
        return {
            "blocks": blocks,
            "failed_optional_blocks": failed_optional_blocks,
            "communication_failed": False,
        }

    def _is_optional_datetime_block(self, register: int, count: int) -> bool:
        block_end = register + count
        block_parameters = []
        for parameter in self.parameters:
            parameter_register = int(parameter["register"])
            parameter_end = parameter_register + self._word_count_for_type(str(parameter["type"]).lower())
            if register <= parameter_register and parameter_end <= block_end:
                block_parameters.append(parameter)
        return bool(block_parameters) and all(
            str(parameter["type"]).lower() == "datetime4" for parameter in block_parameters
        )

    def _get_prefetched_registers(
        self,
        register: int,
        count: int,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[list[int]]:
        if register_state is None:
            return None
        register_blocks = register_state.get("blocks")
        if not isinstance(register_blocks, list):
            return None

        for block_start, regs in register_blocks:
            block_end = block_start + len(regs)
            if block_start <= register and register + count <= block_end:
                offset = register - block_start
                return regs[offset : offset + count]

        failed_optional_blocks = register_state.get("failed_optional_blocks")
        if isinstance(failed_optional_blocks, list):
            for block_start, block_end in failed_optional_blocks:
                if block_start <= register and register + count <= block_end:
                    return None
        return None

    def _read_registers(
        self,
        register: int,
        count: int,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[list[int]]:
        prefetched = self._get_prefetched_registers(register, count, register_state)
        if prefetched is not None:
            return prefetched
        if register_state and register_state.get("communication_failed"):
            return None

        failed_optional_blocks = register_state.get("failed_optional_blocks") if register_state else None
        if isinstance(failed_optional_blocks, list) and any(
            block_start <= register and register + count <= block_end
            for block_start, block_end in failed_optional_blocks
        ):
            return None

        return self.modbus_client.read_holding_registers(
            register,
            count=count,
            one_based=self.one_based_map,
            slave_id=self.slave_id,
            meter_id=self.meter_id,
        )

    def _read_uint16(
        self,
        register: int,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[int]:
        regs = self._read_registers(register, 1, register_state)
        if regs is None:
            return None
        if regs[0] == 0xFFFF:
            return None
        return regs[0]

    def _read_datetime4_raw(
        self,
        register: int,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[str]:
        regs = self._read_registers(register, 4, register_state)
        if regs is None:
            return None
        return "-".join(f"{word:04X}" for word in regs)

    def _read_float32(
        self,
        register: int,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[float]:
        regs = self._read_registers(register, 2, register_state)
        if regs is None:
            return None

        raw_bytes = regs[0].to_bytes(2, "big") + regs[1].to_bytes(2, "big")
        value = struct.unpack(">f", raw_bytes)[0]
        if not math.isfinite(value):
            return None
        return value

    def _read_uint32_lsw(
        self,
        register: int,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[int]:
        regs = self._read_registers(register, 2, register_state)
        if regs is None:
            return None

        # Meter unavailable sentinel.
        if regs[0] == 0xFFFF and regs[1] == 0xFFFF:
            return None

        # Low word first format.
        return (regs[1] << 16) | regs[0]

    def _read_int32_lsw(
        self,
        register: int,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[int]:
        unsigned_value = self._read_uint32_lsw(register, register_state)
        if unsigned_value is None:
            return None
        if unsigned_value & 0x80000000:
            return unsigned_value - 0x100000000
        return unsigned_value

    def _read_int64_lsw(
        self,
        register: int,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[int]:
        regs = self._read_registers(register, 4, register_state)
        if regs is None:
            return None

        # Schneider's register-list definition labels the first register as
        # register 1 but places it in the most-significant 16-bit position:
        # (register 1 << 48) + (register 2 << 32) + (register 3 << 16)
        # + register 4.  The name of this helper is retained for the existing
        # driver interface; this is not the old two-register uint32 decoder.
        unsigned_value = sum(
            (word & 0xFFFF) << (16 * (3 - index))
            for index, word in enumerate(regs)
        )

        # Schneider's unavailable sentinel is 0x8000000000000000, the
        # minimum signed INT64 value.
        if unsigned_value == 0x8000000000000000:
            return None
        if unsigned_value & 0x8000000000000000:
            return unsigned_value - 0x10000000000000000
        return unsigned_value

    def _read_uint64(
        self,
        register: int,
        register_state: Optional[dict[str, object]] = None,
    ) -> Optional[int]:
        regs = self._read_registers(register, 4, register_state)
        if regs is None:
            return None

        # Schneider PM3200/PM3250 energy counters are four consecutive
        # 16-bit words in network order, representing Wh/VARh/VAh.
        if all(word == 0xFFFF for word in regs):
            return None
        return (
            (regs[0] << 48)
            | (regs[1] << 32)
            | (regs[2] << 16)
            | regs[3]
        )


"""
## FILE EXPLANATION
Purpose:
This file implements data collection for Schneider PM5000/EM6400 meters.

Why this file exists:
Each meter model can have its own register map and decoding rules. Keeping
that logic here makes future driver additions straightforward.

What data enters the file:
Raw Modbus registers from ModbusRTUClient and parameter definitions loaded
from meter_config.json.

What data leaves the file:
A dictionary of decoded engineering values keyed by parameter name.

Which layer of the architecture it belongs to:
Collector Layer (device-specific driver).

How it interacts with other files:
Called by services/polling_service.py. Uses collectors/modbus_client.py for
communication and follows collectors/base/base_meter.py interface.
"""
