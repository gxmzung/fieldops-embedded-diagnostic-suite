from dataclasses import dataclass
from typing import Optional

@dataclass
class RmcRecord:
    time_utc: str
    valid: bool
    latitude: Optional[float]
    longitude: Optional[float]
    speed_knots: float

class NmeaParseError(ValueError):
    pass

def verify_checksum(sentence: str) -> bool:
    if not sentence.startswith("$") or "*" not in sentence:
        return False
    body, expected = sentence[1:].split("*", 1)
    checksum = 0
    for ch in body:
        checksum ^= ord(ch)
    return f"{checksum:02X}" == expected.strip().upper()

def ddmm_to_decimal(value: str, hemisphere: str) -> float:
    if not value:
        raise NmeaParseError("missing coordinate")
    dot = value.find(".")
    deg_len = dot - 2
    degrees = int(value[:deg_len])
    minutes = float(value[deg_len:])
    decimal = degrees + minutes / 60.0
    if hemisphere in ("S", "W"):
        decimal *= -1
    return decimal

def parse_gprmc(sentence: str) -> RmcRecord:
    sentence = sentence.strip()
    if not verify_checksum(sentence):
        raise NmeaParseError("checksum failed")

    body = sentence[1:].split("*", 1)[0]
    fields = body.split(",")
    if fields[0] != "GPRMC":
        raise NmeaParseError("not GPRMC")

    valid = fields[2] == "A"
    latitude = ddmm_to_decimal(fields[3], fields[4]) if valid else None
    longitude = ddmm_to_decimal(fields[5], fields[6]) if valid else None
    speed = float(fields[7] or 0.0)

    return RmcRecord(
        time_utc=fields[1],
        valid=valid,
        latitude=latitude,
        longitude=longitude,
        speed_knots=speed
    )
