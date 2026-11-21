"""One-command, localhost-only Phase 3 telemetry diagnostic experiment.

Starts a bounded receiver, injects a deterministic anomaly sequence, waits for
LOST, sends one recovery packet, and validates recorded evidence. No hardware
or RF measurements are claimed.
"""
import argparse
import json
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "03_field_telemetry_monitor" / "telemetry_server.py"
REPORT = ROOT / "03_field_telemetry_monitor" / "event_report.py"
INJECTOR = ROOT / "simulator" / "fault_injector.py"


def read_events(path: Path) -> list:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def wait_for(predicate, timeout: float, proc: subprocess.Popen, reason: str):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        if proc.poll() is not None:
            raise RuntimeError(f"receiver exited early during {reason} (code {proc.returncode})")
        time.sleep(0.025)
    raise TimeoutError(f"timed out waiting for {reason}")


def unused_local_port() -> int:
    # There is a narrow race between port discovery and receiver bind.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def run_experiment(scenario: str = "mixed", count: int = 8,
                   interval: float = 0.05, timeout_seconds: float = 0.45,
                   output_root: Path = ROOT / "out" / "experiments") -> dict:
    if count < 5 or interval < 0 or timeout_seconds <= 0:
        raise ValueError("count >= 5, interval >= 0 and timeout_seconds > 0 required")
    if scenario not in ("normal", "drop", "duplicate", "reorder", "mixed"):
        raise ValueError(f"unknown scenario: {scenario}")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    dest = output_root / run_id
    dest.mkdir(parents=True, exist_ok=False)
    port = unused_local_port()
    log_path = dest / "receiver.log"
    events_path = dest / "events.jsonl"
    csv_path = dest / "telemetry.csv"
    manifest_path = dest / "injection-manifest.json"
    report_path = dest / "report.json"
    config = {
        "run_id": run_id, "scenario": scenario, "count": count,
        "interval_seconds": interval, "timeout_seconds": timeout_seconds,
        "transport": "local UDP loopback (127.0.0.1)",
        "port": port, "recovery_sequence": count,
    }
    (dest / "config.json").write_text(json.dumps(config, indent=2) + "\n",
                                      encoding="utf-8")
    cmd = [
        sys.executable, "-u", str(SERVER), "--host", "127.0.0.1",
        "--port", str(port), "--timeout-seconds", str(timeout_seconds),
        "--run-seconds", "15", "--output", str(csv_path),
        "--events-output", str(events_path),
    ]
    proc = None
    try:
        with log_path.open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(cmd, cwd=ROOT, stdout=log,
                                    stderr=subprocess.STDOUT, text=True)
            wait_for(lambda: log_path.exists() and
                     "listening" in log_path.read_text(encoding="utf-8"),
                     4, proc, "receiver readiness")
            injection = subprocess.run([
                sys.executable, str(INJECTOR),
                "--udp-host", "127.0.0.1", "--udp-port", str(port),
                "--scenario", scenario, "--count", str(count),
                "--interval", str(interval), "--manifest", str(manifest_path),
            ], cwd=ROOT, capture_output=True, text=True, timeout=8, check=True)
            (dest / "injection.log").write_text(injection.stdout, encoding="utf-8")
            expected_sent = len(json.loads(manifest_path.read_text())["sent_sequences"])
            wait_for(lambda: sum(e.get("event_type") == "TELEMETRY"
                                 for e in read_events(events_path)) >= expected_sent,
                     5, proc, "expected packet reception")
            wait_for(lambda: any(e.get("event_type") == "LOST"
                                 for e in read_events(events_path)),
                     max(2.0, timeout_seconds + 1.5), proc, "LOST event")
            # At this point the receiver has already declared LOST.
            from importlib.util import module_from_spec, spec_from_file_location
            spec = spec_from_file_location("fdu_sim", ROOT / "simulator" / "fdu_device_simulator.py")
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            packet = module.make_packet(count)
            packet["protocol_version"] = 1
            packet["sequence_number"] = count
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(json.dumps(packet).encode("utf-8"), ("127.0.0.1", port))
            wait_for(lambda: any(e.get("event_type") == "RECOVERED"
                                 for e in read_events(events_path)),
                     3, proc, "RECOVERED event")
        # The receiver flushes each JSONL event before the predicate succeeds.
    except Exception as exc:
        (dest / "failure.txt").write_text(f"{type(exc).__name__}: {exc}\n",
                                          encoding="utf-8")
        raise
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)

    completed = subprocess.run([
        sys.executable, str(REPORT), "--events", str(events_path),
        "--output", str(report_path),
    ], cwd=ROOT, capture_output=True, text=True, timeout=8, check=True)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    counts = report["event_counts"]
    required = {"CONNECTED": 1, "LOST": 1, "RECOVERED": 1,
                "TELEMETRY": expected_sent + 1}
    if scenario == "mixed":
        required.update({"MISSING_SEQUENCE": 1, "DUPLICATE": 1,
                         "OUT_OF_ORDER": 1})
    failures = {k: {"expected_at_least": v, "actual": counts.get(k, 0)}
                for k, v in required.items() if counts.get(k, 0) < v}
    if report["recorded_recoveries"] < 1:
        failures["recorded_recoveries"] = "expected at least one recovery duration"
    report["experiment_id"] = run_id
    report["scenario"] = scenario
    report["assertion_result"] = "FAIL" if failures else "PASS"
    report["assertion_failures"] = failures
    report["artifacts_directory"] = str(dest)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    if failures:
        raise AssertionError(f"experiment assertions failed: {failures}; see {report_path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="One-command FieldOps diagnostic experiment")
    parser.add_argument("--scenario", choices=["normal", "drop", "duplicate", "reorder", "mixed"],
                        default="mixed")
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--interval", type=float, default=0.05)
    parser.add_argument("--timeout-seconds", type=float, default=0.45)
    parser.add_argument("--output-root", type=Path, default=ROOT / "out" / "experiments")
    args = parser.parse_args()
    try:
        result = run_experiment(args.scenario, args.count, args.interval,
                                args.timeout_seconds, args.output_root)
    except (RuntimeError, TimeoutError, ValueError, OSError, subprocess.SubprocessError,
            AssertionError) as exc:
        print(f"EXPERIMENT FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
