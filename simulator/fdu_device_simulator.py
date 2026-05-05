import argparse
import json
import random
import socket
import time
from datetime import datetime

def make_packet(index: int) -> dict:
    temp = 42.0 + random.random() * 10
    voltage = 12.1 - index * 0.03
    gps_fix = True
    if 10 <= index <= 12:
        temp = 86.0 + random.random() * 2
    if 18 <= index <= 20:
        voltage = 9.6
    if 24 <= index <= 26:
        gps_fix = False

    return {
        "device_id": "FDU01",
        "timestamp": datetime.utcnow().isoformat(),
        "temperature_c": round(temp, 2),
        "voltage_v": round(voltage, 2),
        "current_a": round(1.0 + random.random() * 0.8, 2),
        "lat": round(36.4812 + index * 0.00005, 6),
        "lon": round(127.2891 + index * 0.00005, 6),
        "gps_fix": gps_fix
    }

def run_udp(host: str, port: int, count: int, interval: float) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(count):
        packet = make_packet(i)
        payload = json.dumps(packet).encode("utf-8")
        sock.sendto(payload, (host, port))
        print(f"sent telemetry #{i+1}: {packet}")
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FDU-01 UDP telemetry simulator")
    parser.add_argument("--udp-host", default="127.0.0.1")
    parser.add_argument("--udp-port", type=int, default=9000)
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--interval", type=float, default=0.2)
    args = parser.parse_args()
    run_udp(args.udp_host, args.udp_port, args.count, args.interval)
