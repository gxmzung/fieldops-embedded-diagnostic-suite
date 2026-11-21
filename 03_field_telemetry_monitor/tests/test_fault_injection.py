import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "simulator"))
sys.path.insert(0, str(ROOT / "03_field_telemetry_monitor"))
from fault_injector import sequence_for_scenario, run_scenario
from event_report import summarize


@pytest.mark.parametrize("scenario,expected", [
    ("normal", [0, 1, 2, 3, 4, 5]),
    ("drop", [0, 1, 3, 4, 5]),
    ("duplicate", [0, 1, 2, 3, 3, 4, 5]),
    ("reorder", [0, 1, 3, 2, 4, 5]),
    ("mixed", [0, 1, 3, 3, 2, 4, 5]),
])
def test_scenarios(scenario, expected):
    assert sequence_for_scenario(scenario, 6) == expected


def test_report(tmp_path):
    events = tmp_path / "events.jsonl"
    payload = [
        {"event_type": "CONNECTED", "device_id": "A"},
        {"event_type": "MISSING_SEQUENCE", "device_id": "A", "missing_count": 2},
        {"event_type": "LOST", "device_id": "A"},
        {"event_type": "RECOVERED", "device_id": "A", "downtime_seconds": 0.3},
    ]
    events.write_text("".join(json.dumps(x) + "\n" for x in payload), encoding="utf-8")
    result = summarize(events)
    assert result["observed_sequence_gaps"] == 2
    assert result["event_counts"]["RECOVERED"] == 1
    assert result["mean_detected_downtime_seconds"] == 0.3


def test_real_local_udp_fault_events(tmp_path):
    # Localhost real UDP socket test; not a hardware/network performance benchmark.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    csv_path = tmp_path / "telemetry.csv"
    events_path = tmp_path / "events.jsonl"
    cmd = [
        sys.executable, str(ROOT / "03_field_telemetry_monitor" / "telemetry_server.py"),
        "--port", str(port), "--output", str(csv_path),
        "--events-output", str(events_path), "--run-seconds", "1.5",
        "--timeout-seconds", "0.3",
    ]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True) as proc:
        try:
            # Wait for the server to bind instead of assuming an arbitrary startup delay.
            line = proc.stdout.readline()
            assert "listening" in line.lower()
            run_scenario("127.0.0.1", port, "mixed", 6, 0.025)
            stdout, stderr = proc.communicate(timeout=6)
        except BaseException:
            proc.kill()
            proc.communicate()
            raise
    assert proc.returncode == 0, stderr
    assert csv_path.exists()
    result = summarize(events_path)
    kinds = result["event_counts"]
    assert kinds["TELEMETRY"] == 7
    assert kinds["CONNECTED"] == 1
    assert kinds["MISSING_SEQUENCE"] == 1
    assert kinds["DUPLICATE"] == 1
    assert kinds["OUT_OF_ORDER"] == 1
    assert kinds["LOST"] == 1
    assert result["observed_sequence_gaps"] == 1
