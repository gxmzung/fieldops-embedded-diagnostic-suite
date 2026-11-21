from dataclasses import dataclass
import math


@dataclass
class HealthResult:
    health: str
    message: str


def _finite_number(value, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a JSON number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def validate_telemetry(packet: dict) -> dict:
    """Validate legacy packets and optionally versioned packets.

    Versioned packets may include protocol_version=1 and sequence_number.
    Legacy packets remain valid for the existing simulator.
    """
    if not isinstance(packet, dict):
        raise ValueError("telemetry packet must be an object")
    required = ("device_id", "temperature_c", "voltage_v", "current_a", "gps_fix")
    missing = [key for key in required if key not in packet]
    if missing:
        raise ValueError(f"missing fields: {missing}")
    device_id = packet["device_id"]
    if not isinstance(device_id, str) or not device_id.strip() or len(device_id) > 64:
        raise ValueError("device_id must be a nonempty string of at most 64 characters")
    if not isinstance(packet["gps_fix"], bool):
        raise ValueError("gps_fix must be a JSON boolean")
    temp = _finite_number(packet["temperature_c"], "temperature_c")
    voltage = _finite_number(packet["voltage_v"], "voltage_v")
    current = _finite_number(packet["current_a"], "current_a")
    if not (-100 <= temp <= 250):
        raise ValueError("temperature_c out of supported range")
    if not (0 <= voltage <= 1000):
        raise ValueError("voltage_v out of supported range")
    if not (0 <= current <= 1000):
        raise ValueError("current_a out of supported range")
    if "protocol_version" in packet:
        if type(packet["protocol_version"]) is not int or packet["protocol_version"] != 1:
            raise ValueError("unsupported protocol_version")
    if "sequence_number" in packet:
        seq = packet["sequence_number"]
        if type(seq) is not int or not (0 <= seq <= 4294967295):
            raise ValueError("sequence_number must be a uint32")
    if "timestamp" in packet and not isinstance(packet["timestamp"], str):
        raise ValueError("timestamp must be a string")
    for key, low, high in (("lat", -90, 90), ("lon", -180, 180)):
        if key in packet:
            val = _finite_number(packet[key], key)
            if not low <= val <= high:
                raise ValueError(f"{key} out of range")
    return packet


def classify_telemetry(packet: dict) -> HealthResult:
    try:
        validate_telemetry(packet)
    except ValueError as exc:
        return HealthResult("CRITICAL", f"invalid telemetry: {exc}")

    temp = float(packet["temperature_c"])
    volt = float(packet["voltage_v"])
    gps_fix = packet["gps_fix"]

    if temp >= 85.0:
        return HealthResult("CRITICAL", "temperature critical")
    if volt < 9.8:
        return HealthResult("CRITICAL", "battery critical")
    if not gps_fix:
        return HealthResult("CRITICAL", "gps fix lost")
    if temp >= 70.0:
        return HealthResult("WARN", "temperature elevated")
    if volt < 10.5:
        return HealthResult("WARN", "battery voltage low")
    return HealthResult("NORMAL", "nominal")
