import argparse
import csv
import json
import socket
import time
from pathlib import Path
from typing import Optional

from diagnostic_state import DiagnosticTracker
from health_checker import classify_telemetry, validate_telemetry


def run_server(host: str, port: int, output: Path, max_packets: Optional[int] = None,
               timeout_seconds: float = 5.0) -> None:
    if max_packets is not None and max_packets <= 0:
        raise ValueError("max_packets must be positive")
    tracker = DiagnosticTracker(timeout_seconds)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        sock.settimeout(min(0.5, timeout_seconds / 2))
        print(f"Telemetry server listening on udp://{host}:{port}")
        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "device_id", "temperature_c", "voltage_v",
                "current_a", "gps_fix", "health", "message"
            ])
            writer.writeheader()
            while True:
                try:
                    data, addr = sock.recvfrom(4096)
                except socket.timeout:
                    data = None
                if data is not None:
                    count += 1
                    try:
                        packet = json.loads(data.decode("utf-8"))
                        validate_telemetry(packet)
                        result = classify_telemetry(packet)
                        events = tracker.observe(packet["device_id"], time.monotonic(),
                                                 packet.get("sequence_number"))
                        row = {
                            "timestamp": packet.get("timestamp", ""),
                            "device_id": packet["device_id"],
                            "temperature_c": packet["temperature_c"],
                            "voltage_v": packet["voltage_v"],
                            "current_a": packet["current_a"],
                            "gps_fix": packet["gps_fix"],
                            "health": result.health,
                            "message": result.message,
                        }
                        writer.writerow(row)
                        f.flush()
                        print(f"[{result.health}] {packet['device_id']}: {result.message}")
                        for event in events:
                            print(f"[TRANSPORT] {packet['device_id']}: {event}")
                    except (ValueError, TypeError, UnicodeError) as exc:
                        print(f"[REJECTED] invalid telemetry from {addr}: {exc}")
                for device_id in tracker.check_timeouts(time.monotonic()):
                    print(f"[LOST] {device_id}: telemetry timeout ({timeout_seconds}s)")
                if max_packets is not None and count >= max_packets:
                    break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FDU-01 UDP telemetry monitor")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--output", default="data/telemetry_events.csv")
    parser.add_argument("--max-packets", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    args = parser.parse_args()
    run_server(args.host, args.port, Path(args.output), args.max_packets,
               args.timeout_seconds)
