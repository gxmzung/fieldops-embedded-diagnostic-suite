from dataclasses import dataclass

@dataclass
class SensorRecord:
    device_id: str
    temperature_c: float
    voltage_v: float
    current_a: float
    status: str

class SensorParseError(ValueError):
    pass

def parse_sensor_line(line: str) -> SensorRecord:
    line = line.strip()
    parts = line.split(",")
    if len(parts) != 5:
        raise SensorParseError(f"invalid field count: {line}")

    device_id = parts[0]
    values = {}
    for item in parts[1:]:
        if "=" not in item:
            raise SensorParseError(f"invalid key-value field: {item}")
        key, value = item.split("=", 1)
        values[key] = value

    try:
        return SensorRecord(
            device_id=device_id,
            temperature_c=float(values["TEMP"]),
            voltage_v=float(values["VOLT"]),
            current_a=float(values["CURR"]),
            status=values["STATUS"],
        )
    except KeyError as exc:
        raise SensorParseError(f"missing field: {exc}") from exc
    except ValueError as exc:
        raise SensorParseError(f"numeric conversion failed: {line}") from exc

def classify_sensor(record: SensorRecord) -> str:
    if record.temperature_c >= 85.0 or record.voltage_v < 9.8:
        return "CRITICAL"
    if record.temperature_c >= 70.0 or record.voltage_v < 10.5 or record.status != "OK":
        return "WARN"
    return "NORMAL"
