# Phase 2 — Repeatable UDP Fault Injection and Evidence

This phase adds deterministic **sender-side** application datagram injection and
receiver-side JSONL evidence. It is not a radio-link measurement and does not
validate physical equipment, packet integrity or delivery guarantees.

## Prerequisites
- Python 3.9 or newer
- `python3 -m pip install -r requirements.txt`

## macOS demo (two terminals)

Terminal A — run the capture for 3 seconds:
```bash
mkdir -p out
python3 03_field_telemetry_monitor/telemetry_server.py \
  --host 127.0.0.1 --port 9000 --timeout-seconds 0.7 \
  --run-seconds 3 --output out/telemetry.csv \
  --events-output out/diagnostic-events.jsonl
```

Terminal B — start after A displays `listening`:
```bash
python3 simulator/fault_injector.py \
  --scenario mixed --count 8 --interval 0.05 \
  --manifest out/injection-manifest.json
```

After Terminal A exits:
```bash
python3 03_field_telemetry_monitor/event_report.py \
  --events out/diagnostic-events.jsonl \
  --output out/diagnostic-report.json
python3 -m pytest -q
```

The expected `mixed` sender sequences are
`[0, 1, 3, 3, 2, 4, 5, 6, 7]`.
After the first receiver observation, expect:
- one forward-gap event with missing_count=1;
- one DUPLICATE event;
- one OUT_OF_ORDER event;
- one LOST event if the capture stays active at least one timeout after the final valid packet.

The report includes event totals, per-device counts, sequence-gap totals
and any observed recovery durations.

## Event semantics
- A sequence gap does **not** prove datagrams were lost in a real network:
  intentional sender omission or reordering may produce the same signal.
- The `mixed` scenario intentionally causes a gap *then* supplies its old
  packet: gap counters are **observed forward gaps, not permanent losses**.
- `LOST` means the receiver observed silence for its configured local
  timeout. `RECOVERED` means accepted telemetry arrived afterward.
- `downtime_seconds` begins at the moment the server first **detects**
  LOST; it excludes the preceding detection threshold.
- UDP on loopback is tested automatically. Neither real RF impairment nor
  deterministic delivery is guaranteed by this harness.
- Events are emitted as JSON Lines, with UTC receive timestamps.
- There is no authentication, CRC or cryptographic validation in this phase.

## Operational caution
Default `data/telemetry_events.csv` is tracked by Git. For experiments
use `--output out/telemetry.csv`, not the tracked sample file.
Review `git status` before committing.
