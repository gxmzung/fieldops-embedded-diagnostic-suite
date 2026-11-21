import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(sys.platform == "win32", reason="requires POSIX PTY")
def test_virtual_uart_end_to_end(tmp_path):
    process = subprocess.run([
        sys.executable, str(ROOT / "tools" / "run_virtual_uart_experiment.py"),
        "--output-root", str(tmp_path), "--timeout-seconds", "0.25",
    ], cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report["assertion_result"] == "PASS"
    assert report["event_counts"]["TELEMETRY"] == 3
    assert report["event_counts"]["CONNECTED"] == 1
    assert report["event_counts"]["LOST"] == 1
    assert report["event_counts"]["RECOVERED"] == 1
    assert report["recorded_recoveries"] == 1
    dest = Path(report["artifacts_directory"])
    for filename in ("config.json", "receiver.log", "bridge.log",
                     "telemetry.csv", "events.jsonl", "report.json"):
        assert (dest / filename).exists(), filename
