"""Phase 4 virtual UART lab: PTY->parser->UDP->receiver, with silence/recovery."""
import argparse
import json
import os
import pty
import select
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "01_serial_sensor_gateway" / "uart_udp_bridge.py"
SERVER = ROOT / "03_field_telemetry_monitor" / "telemetry_server.py"
REPORT = ROOT / "03_field_telemetry_monitor" / "event_report.py"


def events(path):
    if not path.exists():
        return []
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s]


def wait_for(predicate, seconds, procs):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        if any(p.poll() is not None for p in procs):
            raise RuntimeError("child process exited unexpectedly; see logs")
        time.sleep(0.025)
    raise TimeoutError("expected condition not observed; see logs")


def run(output_root: Path, timeout_seconds: float = 0.35) -> dict:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    dest = output_root / run_id
    dest.mkdir(parents=True, exist_ok=False)
    master, slave = pty.openpty()
    device = os.ttyname(slave)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    event_path = dest / "events.jsonl"
    report_path = dest / "report.json"
    config = {"run_id": run_id, "device": device, "port": port,
              "source": "macOS/Linux POSIX PTY (synthetic UART bytes)",
              "timeout_seconds": timeout_seconds,
              "gps_fix": "synthetically assumed true for demonstration",
              "silence": "paused writer; NOT USB disconnection"}
    (dest / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    children = []
    try:
        with (dest / "receiver.log").open("w") as receiver_log, (dest / "bridge.log").open("w") as bridge_log:
            receiver = subprocess.Popen([
                sys.executable, "-u", str(SERVER), "--host", "127.0.0.1",
                "--port", str(port), "--timeout-seconds", str(timeout_seconds),
                "--run-seconds", "12", "--output", str(dest / "telemetry.csv"),
                "--events-output", str(event_path),
            ], cwd=ROOT, stdout=receiver_log, stderr=subprocess.STDOUT)
            children.append(receiver)
            wait_for(lambda: "listening" in (dest / "receiver.log").read_text(), 3, children)
            bridge = subprocess.Popen([
                sys.executable, "-u", str(BRIDGE), "--device", device,
                "--host", "127.0.0.1", "--port", str(port),
                "--assume-gps-fix",
            ], cwd=ROOT, stdout=bridge_log, stderr=subprocess.STDOUT)
            children.append(bridge)
            wait_for(lambda: "bridge ready" in (dest / "bridge.log").read_text(),
                     3, children)
            def send(temp):
                line = f"FDU01,TEMP={temp},VOLT=12.0,CURR=1.2,STATUS=OK\n"
                os.write(master, line.encode("ascii"))
            send(42)
            send(44)
            wait_for(lambda: sum(e.get("event_type") == "TELEMETRY" for e in events(event_path)) == 2,
                     3, children)
            # No UART bytes while receiver remains open: application-layer silence.
            wait_for(lambda: any(e.get("event_type") == "LOST" for e in events(event_path)),
                     max(2, timeout_seconds + 1.2), children)
            send(46)
            wait_for(lambda: any(e.get("event_type") == "RECOVERED" for e in events(event_path)),
                     3, children)
    except Exception as exc:
        (dest / "failure.txt").write_text(f"{type(exc).__name__}: {exc}\n")
        raise
    finally:
        for proc in children:
            if proc.poll() is None:
                proc.terminate()
        for proc in children:
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
        os.close(master)
        os.close(slave)
    subprocess.run([sys.executable, str(REPORT), "--events", str(event_path),
                    "--output", str(report_path)], cwd=ROOT, check=True,
                   capture_output=True, timeout=8)
    result = json.loads(report_path.read_text())
    counts = result["event_counts"]
    required = {"TELEMETRY": 3, "CONNECTED": 1, "LOST": 1, "RECOVERED": 1}
    errors = {k: {"expected": v, "actual": counts.get(k, 0)}
              for k,v in required.items() if counts.get(k, 0) != v}
    result.update({"experiment_id": run_id, "experiment_type": "virtual-uart",
                   "assertion_result": "FAIL" if errors else "PASS",
                   "assertion_failures": errors, "artifacts_directory": str(dest)})
    report_path.write_text(json.dumps(result, indent=2) + "\n")
    if errors:
        raise AssertionError(f"virtual UART evidence mismatch: {errors}")
    return result


def main():
    ap = argparse.ArgumentParser(description="Virtual UART/PTTY diagnostic experiment")
    ap.add_argument("--output-root", type=Path, default=ROOT / "out" / "virtual-uart")
    ap.add_argument("--timeout-seconds", type=float, default=0.35)
    args = ap.parse_args()
    try:
        result = run(args.output_root, args.timeout_seconds)
    except (OSError, RuntimeError, TimeoutError, ValueError, subprocess.SubprocessError,
            AssertionError) as exc:
        ap.exit(1, f"EXPERIMENT FAILED: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
