import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools" / "run_diagnostic_experiment.py"


def test_one_command_mixed_end_to_end(tmp_path):
    result = subprocess.run([
        sys.executable, str(RUNNER), "--scenario", "mixed",
        "--count", "6", "--interval", "0.03",
        "--timeout-seconds", "0.25", "--output-root", str(tmp_path),
    ], cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["assertion_result"] == "PASS"
    assert report["event_counts"]["TELEMETRY"] == 8
    assert report["event_counts"]["CONNECTED"] == 1
    assert report["event_counts"]["LOST"] >= 1
    assert report["event_counts"]["RECOVERED"] >= 1
    assert report["event_counts"]["DUPLICATE"] == 1
    assert report["event_counts"]["OUT_OF_ORDER"] == 1
    assert report["observed_sequence_gaps"] == 1
    assert report["recorded_recoveries"] >= 1
    dest = Path(report["artifacts_directory"])
    for name in ("config.json", "receiver.log", "injection-manifest.json",
                 "events.jsonl", "telemetry.csv", "report.json"):
        assert (dest / name).is_file(), name
