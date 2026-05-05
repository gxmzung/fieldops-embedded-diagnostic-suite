from dataclasses import dataclass

@dataclass
class HealthResult:
    health: str
    message: str

def classify_telemetry(packet: dict) -> HealthResult:
    required = ["device_id", "temperature_c", "voltage_v", "current_a", "gps_fix"]
    missing = [key for key in required if key not in packet]
    if missing:
        return HealthResult("CRITICAL", f"missing fields: {missing}")

    temp = float(packet["temperature_c"])
    volt = float(packet["voltage_v"])
    gps_fix = bool(packet["gps_fix"])

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
