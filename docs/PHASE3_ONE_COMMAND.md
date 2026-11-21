# Phase 3: One-command reproducible diagnostic experiment

Run on macOS or Linux (Python 3.9+):

```bash
cd ~/dev/fieldops-embedded-diagnostic-suite
source .venv/bin/activate
python tools/run_diagnostic_experiment.py
```

Optional: `--scenario mixed --count 8 --interval 0.05 --timeout-seconds 0.45`.

This tool:
1. Creates a unique UTC run directory under `out/experiments/`.
2. Reserves a candidate localhost UDP port and launches the receiver.
3. Waits for receiver readiness before injecting faults.
4. Confirms all intended application datagrams were observed on local loopback.
5. Waits for receiver LOST and sends a new telemetry packet to trigger RECOVERED.
6. Collects JSONL evidence, CSV telemetry, diagnostic report, config and receiver log.
7. Validates expected event counts and exits nonzero on failure.

A report `assertion_result=PASS` establishes only that expected events
were observed in this **local scripted scenario**. It does not prove radio
packet loss, deployed-equipment recovery time, a secure or fault-tolerant
transport, or production suitability.

`mean_detected_downtime_seconds` measures the time from **LOST detection**
to the recovery observation, not the full time since the last good packet.
The receiver is intentionally terminated immediately after recovery is
recorded; that termination is orchestrated by the runner.

Tests: `python -m pytest -q`.

Known limitations: dynamic UDP port discovery has a narrow time-of-check/time-of-use
race; runner fails rather than masking a failed receiver bind. Experiment run
identifiers are UTC timestamps, not a globally coordinated registry.
