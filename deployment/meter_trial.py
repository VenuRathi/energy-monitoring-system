from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _add_repo_to_path(project_root: Path) -> None:
    sys.path.insert(0, str(project_root))


def _word_count(parameter_type: str) -> int:
    normalized = parameter_type.lower().strip()
    if normalized == "datetime4":
        return 4
    if normalized == "uint16":
        return 1
    return 2


def _connection_value(connection: dict[str, Any], key: str, fallback: Any) -> Any:
    return connection.get(key, fallback)


def run(project_root: Path, output_path: Path) -> int:
    _add_repo_to_path(project_root)

    from serial.tools import list_ports

    from app.collectors.modbus_client import ModbusRTUClient
    from config.meter_loader import load_meter_config

    meter_config = load_meter_config(str(project_root / "config" / "meter_config.json"))
    detected_ports = sorted(str(port.device).upper() for port in list_ports.comports() if getattr(port, "device", None))
    detected_port_set = set(detected_ports)

    results: list[dict[str, Any]] = []
    for meter in meter_config.get("meters", []):
        if not bool(meter.get("enabled", True)):
            results.append(
                {
                    "meter_id": meter.get("meter_id", "unknown-meter"),
                    "status": "SKIP",
                    "message": "meter is disabled",
                }
            )
            continue

        connection = dict(meter.get("connection") or {})
        port = str(connection.get("com_port") or connection.get("port", "")).upper()
        slave_id = int(_connection_value(connection, "slave_id", 1))
        if not port:
            results.append(
                {
                    "meter_id": meter.get("meter_id", "unknown-meter"),
                    "status": "FAIL",
                    "message": "enabled meter has no COM port configured",
                }
            )
            continue

        if detected_port_set and port not in detected_port_set:
            results.append(
                {
                    "meter_id": meter.get("meter_id", "unknown-meter"),
                    "status": "FAIL",
                    "port": port,
                    "slave_id": slave_id,
                    "message": f"configured port {port} was not detected by Windows",
                }
            )
            continue

        parameters = meter.get("parameters") or []
        if not parameters:
            results.append(
                {
                    "meter_id": meter.get("meter_id", "unknown-meter"),
                    "status": "FAIL",
                    "port": port,
                    "slave_id": slave_id,
                    "message": "meter has no parameters to test",
                }
            )
            continue

        parameter = parameters[0]
        register = int(parameter["register"])
        count = _word_count(str(parameter.get("type", "float32")))
        client = ModbusRTUClient(
            port=port,
            baud_rate=int(_connection_value(connection, "baud_rate", 9600)),
            parity=str(_connection_value(connection, "parity", "N")),
            stop_bits=int(_connection_value(connection, "stop_bits", 1)),
            byte_size=int(_connection_value(connection, "byte_size", 8)),
            slave_id=slave_id,
            timeout=float(_connection_value(connection, "timeout", 2.0)),
            reconnect_interval_seconds=0.0,
        )
        try:
            registers = client.read_holding_registers(
                register,
                count,
                one_based=bool(_connection_value(connection, "one_based_map", True)),
                slave_id=slave_id,
                meter_id=str(meter.get("meter_id", "unknown-meter")),
            )
            if registers is None:
                results.append(
                    {
                        "meter_id": meter.get("meter_id", "unknown-meter"),
                        "status": "FAIL",
                        "port": port,
                        "slave_id": slave_id,
                        "register": register,
                        "message": "no Modbus response for trial register",
                    }
                )
            else:
                results.append(
                    {
                        "meter_id": meter.get("meter_id", "unknown-meter"),
                        "status": "PASS",
                        "port": port,
                        "slave_id": slave_id,
                        "register": register,
                        "parameter": parameter.get("name", ""),
                        "raw_registers": registers,
                        "message": "Modbus trial read returned registers",
                    }
                )
        except Exception as exc:
            results.append(
                {
                    "meter_id": meter.get("meter_id", "unknown-meter"),
                    "status": "FAIL",
                    "port": port,
                    "slave_id": slave_id,
                    "register": register,
                    "message": f"{type(exc).__name__}: {exc}",
                }
            )
        finally:
            client.close()

    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "detected_ports": detected_ports,
        "trials": results,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0 if not any(item["status"] == "FAIL" for item in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run direct Modbus trials for configured meters.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    return run(Path(args.project_root).resolve(), Path(args.output).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
