from datetime import datetime, timedelta
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

def generate_sensor_uart(path: Path, count: int = 60) -> None:
    lines = []
    for i in range(count):
        temp = 40 + random.random() * 20
        volt = 12.2 - i * 0.025
        curr = 1.0 + random.random() * 0.8
        status = "OK"
        if i in (20, 21, 22):
            temp = 86 + random.random() * 3
            status = "WARN"
        if i in (40, 41):
            volt = 9.5
            status = "FAULT"
        lines.append(f"FDU01,TEMP={temp:.1f},VOLT={volt:.2f},CURR={curr:.2f},STATUS={status}")
    lines.insert(7, "CORRUPTED_LINE")
    lines.insert(33, "FDU01,TEMP=BAD,VOLT=11.3,CURR=1.2,STATUS=OK")
    path.write_text("\n".join(lines), encoding="utf-8")

def checksum(sentence_body: str) -> str:
    c = 0
    for ch in sentence_body:
        c ^= ord(ch)
    return f"{c:02X}"

def generate_nmea(path: Path, count: int = 30) -> None:
    lines = []
    lat_base = 3628.8000  # 36 deg 28.8000 min
    lon_base = 12717.4000 # 127 deg 17.4000 min
    for i in range(count):
        hhmmss = f"120{i:02d}00"[:6]
        status = "A"
        if i in (12, 13):
            status = "V"
        lat = lat_base + i * 0.003
        lon = lon_base + i * 0.004
        speed = 10.0 + i * 0.1
        body = f"GPRMC,{hhmmss},{status},{lat:.4f},N,{lon:.4f},E,{speed:.1f},084.4,050526,,,A"
        lines.append(f"${body}*{checksum(body)}")
    path.write_text("\n".join(lines), encoding="utf-8")

def generate_events(path: Path, count: int = 80) -> None:
    now = datetime(2026, 5, 5, 14, 0, 0)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "device_id", "temperature_c", "voltage_v",
            "current_a", "gps_fix", "health", "message"
        ])
        writer.writeheader()
        for i in range(count):
            ts = now + timedelta(seconds=i * 10)
            temp = 42 + random.random() * 8
            volt = 12.1 - i * 0.015
            gps_fix = "true"
            health = "NORMAL"
            msg = "nominal"
            if 30 <= i < 36:
                temp = 75 + random.random() * 8
                health = "WARN"
                msg = "temperature elevated"
            if 45 <= i < 49:
                volt = 9.6
                health = "CRITICAL"
                msg = "battery critical"
            if 60 <= i < 64:
                gps_fix = "false"
                health = "CRITICAL"
                msg = "gps fix lost"
            writer.writerow({
                "timestamp": ts.isoformat(),
                "device_id": "FDU01",
                "temperature_c": f"{temp:.1f}",
                "voltage_v": f"{volt:.2f}",
                "current_a": f"{1.0 + random.random():.2f}",
                "gps_fix": gps_fix,
                "health": health,
                "message": msg
            })

if __name__ == "__main__":
    generate_sensor_uart(DATA / "sensor_uart.txt")
    generate_nmea(DATA / "sample_nmea.txt")
    generate_events(DATA / "equipment_events.csv")
    print(f"Generated sample data in {DATA}")
