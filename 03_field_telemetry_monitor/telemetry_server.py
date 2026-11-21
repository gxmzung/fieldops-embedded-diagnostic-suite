import argparse
import csv
import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from diagnostic_state import DiagnosticTracker
from health_checker import classify_telemetry, validate_telemetry


def record_event(stream, event_type: str, device_id: str, **details) -> None:
    if stream is None:
        return
    event = {
        "received_at_utc": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "device_id": device_id,
        **details,
    }
    stream.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")
    stream.flush()


def run_server(host: str, port: int, output: Path, max_packets: Optional[int] = None,
               timeout_seconds: float = 5.0, events_output: Optional[Path] = None,
               run_seconds: Optional[float] = None) -> None:
    if max_packets is not None and max_packets <= 0:
        raise ValueError("max_packets must be positive")
    if run_seconds is not None and run_seconds <= 0:
        raise ValueError("run_seconds must be positive")
    tracker = DiagnosticTracker(timeout_seconds)
    output.parent.mkdir(parents=True, exist_ok=True)
    if events_output is not None:
        events_output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    started = time.monotonic()
    lost_at = {}

    # ExitStack makes the optional event stream safe without changing CLI CSV output.
    from contextlib import ExitStack
    with ExitStack() as stack:
        f = stack.enter_context(output.open("w", newline="", encoding="utf-8"))
        events_stream = (stack.enter_context(events_output.open("w", encoding="utf-8"))
                         if events_output is not None else None)
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "device_id", "temperature_c", "voltage_v",
            "current_a", "gps_fix", "health", "message"
        ])
        writer.writeheader()
        sock = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        sock.bind((host, port))
        sock.settimeout(min(0.2, timeout_seconds / 2))
        print(f"Telemetry server listening on udp://{host}:{port}", flush=True)
        while True:
            if run_seconds is not None and time.monotonic() - started >= run_seconds:
                break
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
                    now = time.monotonic()
                    device = packet["device_id"]
                    events = tracker.observe(device, now, packet.get("sequence_number"))
                    row = {
                        "timestamp": packet.get("timestamp", ""),
                        "device_id": device,
                        "temperature_c": packet["temperature_c"],
                        "voltage_v": packet["voltage_v"],
                        "current_a": packet["current_a"],
                        "gps_fix": packet["gps_fix"],
                        "health": result.health,
                        "message": result.message,
                    }
                    writer.writerow(row)
                    f.flush()
                    record_event(events_stream, "TELEMETRY", device, health=result.health,
                                 sequence_number=packet.get("sequence_number"))
                    print(f"[{result.health}] {device}: {result.message}", flush=True)
                    for event in events:
                        if event.startswith("MISSING_SEQUENCE:"):
                            missing = int(event.split(":", 1)[1])
                            record_event(events_stream, "MISSING_SEQUENCE", device,
                                         missing_count=missing)
                        elif event == "RECOVERED":
                            downtime = now - lost_at.pop(device, now)
                            record_event(events_stream, "RECOVERED", device,
                                         downtime_seconds=round(downtime, 6))
                        else:
                            record_event(events_stream, event, device)
                        print(f"[TRANSPORT] {device}: {event}", flush=True)
                except (ValueError, TypeError, UnicodeError) as exc:
                    record_event(events_stream, "REJECTED", "UNKNOWN", reason=str(exc),
                                 source_ip=addr[0])
                    print(f"[REJECTED] invalid telemetry from {addr}: {exc}", flush=True)
            now = time.monotonic()
            for device in tracker.check_timeouts(now):
                lost_at[device] = now
                record_event(events_stream, "LOST", device, timeout_seconds=timeout_seconds)
                print(f"[LOST] {device}: telemetry timeout ({timeout_seconds}s)", flush=True)
            if max_packets is not None and count >= max_packets:
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FDU-01 UDP telemetry monitor")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--output", type=Path, default=Path("data/telemetry_events.csv"))
    parser.add_argument("--max-packets", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--events-output", type=Path, default=None,
                        help="Optional JSONL diagnostic event output")
    parser.add_argument("--run-seconds", type=float, default=None,
                        help="Optional bounded capture for deterministic experiments")
    args = parser.parse_args()
    run_server(args.host, args.port, args.output, args.max_packets,
               args.timeout_seconds, args.events_output, args.run_seconds)
