"""UART ASCII record parser with opt-in CRC32 and strict field validation.

Legacy wire format: FDU01,TEMP=42.3,VOLT=11.8,CURR=1.2,STATUS=OK
CRC format: legacy ASCII bytes followed by * and eight uppercase hex digits.
CRC32 detects accidental corruption; it is not authentication.
"""
from dataclasses import dataclass
import math
import re
import zlib


@dataclass
class SensorRecord:
    device_id: str
    temperature_c: float
    voltage_v: float
    current_a: float
    status: str


class SensorParseError(ValueError):
    pass


FIELDS = frozenset(("TEMP", "VOLT", "CURR", "STATUS"))
DEVICE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
CRC_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$")


def append_crc32(payload: str) -> str:
    """Return payload plus CRC32 over exact ASCII bytes (excluding suffix/newline)."""
    if not payload or "*" in payload:
        raise ValueError("invalid payload for CRC")
    return f"{payload}*{zlib.crc32(payload.encode('ascii')):08X}"


def parse_sensor_line(line: str, require_crc: bool = False) -> SensorRecord:
    if not isinstance(line, str):
        raise SensorParseError("line must be text")
    line = line.strip()
    if len(line) > 512 or not line or any(ord(ch) > 127 or ord(ch) < 32 for ch in line):
        raise SensorParseError("invalid ASCII record")
    if "*" in line:
        if line.count("*") != 1:
            raise SensorParseError("invalid CRC suffix count")
        payload, suffix = line.rsplit("*", 1)
        if not CRC_PATTERN.fullmatch(suffix):
            raise SensorParseError("CRC suffix must contain exactly eight hex digits")
        actual = zlib.crc32(payload.encode("ascii"))
        if actual != int(suffix, 16):
            raise SensorParseError("CRC32 mismatch")
    else:
        if require_crc:
            raise SensorParseError("CRC32 required")
        payload = line
    parts = payload.split(",")
    if len(parts) != 5:
        raise SensorParseError("invalid field count")
    device_id = parts[0]
    if not DEVICE_PATTERN.fullmatch(device_id):
        raise SensorParseError("invalid device_id")
    values = {}
    for item in parts[1:]:
        if item.count("=") != 1:
            raise SensorParseError("invalid key-value field")
        key, value = item.split("=", 1)
        if key not in FIELDS or key in values or not value:
            raise SensorParseError("unknown, duplicate, or empty field")
        values[key] = value
    if values.keys() != FIELDS:
        raise SensorParseError("missing fields")
    if values["STATUS"] not in ("OK", "WARN", "ERROR"):
        raise SensorParseError("invalid status")
    try:
        temp = float(values["TEMP"])
        voltage = float(values["VOLT"])
        current = float(values["CURR"])
    except ValueError as exc:
        raise SensorParseError("numeric conversion failed") from exc
    if not all(math.isfinite(x) for x in (temp, voltage, current)):
        raise SensorParseError("non-finite measurement")
    if not (-100 <= temp <= 250 and 0 <= voltage <= 1000 and 0 <= current <= 1000):
        raise SensorParseError("measurement outside supported range")
    return SensorRecord(device_id, temp, voltage, current, values["STATUS"])


def classify_sensor(record: SensorRecord) -> str:
    if record.temperature_c >= 85.0 or record.voltage_v < 9.8:
        return "CRITICAL"
    if record.temperature_c >= 70.0 or record.voltage_v < 10.5 or record.status != "OK":
        return "WARN"
    return "NORMAL"


class LineFramer:
    """Bounded, newline-delimited byte framer that resynchronizes after oversize."""
    def __init__(self, max_bytes: int = 512):
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.max_bytes = max_bytes
        self._buffer = bytearray()
        self._dropping = False

    def feed(self, chunk: bytes):
        """Yield (line_bytes, error) pairs; an oversize line emits one error."""
        for byte in chunk:
            if byte == 10:
                if self._dropping:
                    self._dropping = False
                else:
                    yield bytes(self._buffer), None
                self._buffer.clear()
            elif not self._dropping:
                if len(self._buffer) >= self.max_bytes:
                    self._buffer.clear()
                    self._dropping = True
                    yield None, "UART frame too long"
                else:
                    self._buffer.append(byte)
