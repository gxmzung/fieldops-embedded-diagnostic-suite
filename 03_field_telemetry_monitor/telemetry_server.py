import argparse
import csv
import json
import socket
from pathlib import Path
from typing import Optional
from health_checker import classify_telemetry

def run_server(host: str, port: int, output: Path, max_packets: Optional[int] = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"Telemetry server listening on udp://{host}:{port}")

    count = 0
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "device_id", "temperature_c", "voltage_v", "current_a",
            "gps_fix", "health", "message"
        ])
        writer.writeheader()

        while True:
            data, addr = sock.recvfrom(4096)
            try:
                packet = json.loads(data.decode("utf-8"))
                result = classify_telemetry(packet)
                row = {
                    "timestamp": packet.get("timestamp", ""),
                    "device_id": packet.get("device_id", "UNKNOWN"),
                    "temperature_c": packet.get("temperature_c", ""),
                    "voltage_v": packet.get("voltage_v", ""),
                    "current_a": packet.get("current_a", ""),
                    "gps_fix": packet.get("gps_fix", ""),
                    "health": result.health,
                    "message": result.message,
                }
                writer.writerow(row)
                f.flush()
                print(f"[{result.health}] {row['device_id']} temp={row['temperature_c']} volt={row['voltage_v']} msg={result.message}")
            except Exception as exc:
                print(f"[CRITICAL] invalid telemetry from {addr}: {exc}")

            count += 1
            if max_packets is not None and count >= max_packets:
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP telemetry monitor for FDU-01")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--output", default="data/telemetry_events.csv")
    parser.add_argument("--max-packets", type=int, default=None)
    args = parser.parse_args()

    run_server(args.host, args.port, Path(args.output), args.max_packets)
