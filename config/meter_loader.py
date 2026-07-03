import json


def load_meter_config(path: str = "config/meter_config.json") -> dict:
    with open(path, "r", encoding="utf-8") as file:
        raw_config = json.load(file)

    meter_defaults = dict(raw_config.get("meter_defaults", {}))
    connection_defaults = dict(raw_config.get("connection_defaults", {}))
    parameter_sets = dict(raw_config.get("parameter_sets", {}))

    normalized_meters = []
    for meter in raw_config.get("meters", []):
        normalized_meter = dict(meter_defaults)
        normalized_meter.update(meter)

        normalized_connection = dict(connection_defaults)
        normalized_connection.update(meter.get("connection", {}))
        normalized_meter["connection"] = normalized_connection

        parameter_set_name = normalized_meter.get("parameter_set")
        has_inline_parameters = "parameters" in normalized_meter
        if parameter_set_name and has_inline_parameters:
            raise ValueError(
                f"Meter '{normalized_meter.get('meter_id', 'unknown')}' cannot define both 'parameter_set' and inline 'parameters'."
            )

        if parameter_set_name:
            if parameter_set_name not in parameter_sets:
                raise ValueError(
                    f"Meter '{normalized_meter.get('meter_id', 'unknown')}' references unknown parameter_set '{parameter_set_name}'."
                )
            normalized_meter["parameters"] = [dict(parameter) for parameter in parameter_sets[parameter_set_name]]
        elif has_inline_parameters:
            normalized_meter["parameters"] = [dict(parameter) for parameter in normalized_meter["parameters"]]
        else:
            raise ValueError(
                f"Meter '{normalized_meter.get('meter_id', 'unknown')}' must define either 'parameter_set' or 'parameters'."
            )

        normalized_meters.append(normalized_meter)

    normalized_config = dict(raw_config)
    normalized_config["meters"] = normalized_meters
    return normalized_config