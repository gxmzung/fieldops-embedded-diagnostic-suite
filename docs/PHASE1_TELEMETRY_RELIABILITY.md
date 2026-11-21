# Phase 1: Telemetry reliability

## Scope
- Strict input checking for device identity, booleans, finite numeric measurements and optional v1 envelope metadata.
- Per-device monotonic-clock heartbeat timeout with CONNECTED, LOST and RECOVERED console events.
- Optional uint32 sequence_number tracking for duplicates, reverse-order arrivals and forward gaps.
- Existing unversioned simulator JSON remains supported.

## Run
Terminal A:
```bash
python3 03_field_telemetry_monitor/telemetry_server.py --timeout-seconds 5
```
Terminal B:
```bash
python3 simulator/fdu_device_simulator.py --count 30
```
Tests:
```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
make -C 04_embedded_task_scheduler
```

Dashboard:
```bash
python3 06_web_dashboard/dashboard.py
# http://127.0.0.1:8080/06_web_dashboard/
```

## Important semantics and limitations
- LOST means no accepted telemetry for the configured receiver-local interval; it is not evidence of a specific radio failure.
- MISSING_SEQUENCE is a gap in observed application sequence numbers, not a physical-layer packet-loss measurement.
- Existing packets may omit sequence_number. Gaps and duplicates cannot be inferred for those devices.
- Protocol version 1 is a metadata convention, **not** an authenticated or integrity-protected transport protocol.
- No CRC, cryptographic authentication, device reconnect controls, or hardware-in-the-loop test has been added yet.
- Console transport events are not yet persisted to the original telemetry CSV.
- This remains a development/simulation toolkit, not a production safety system.
