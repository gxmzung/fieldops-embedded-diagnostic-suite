"""Summarize structured FieldOps diagnostic events from JSON Lines."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def summarize(events_path: Path) -> dict:
    if not events_path.exists():
        raise FileNotFoundError(events_path)
    counts = Counter()
    devices = defaultdict(Counter)
    missing_sequences = 0
    recovery_seconds = []
    rows = 0
    with events_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                kind = event["event_type"]
                device_id = event["device_id"]
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"invalid event at line {line_number}: {exc}") from exc
            if not isinstance(kind, str) or not isinstance(device_id, str):
                raise ValueError(f"invalid event at line {line_number}: wrong field types")
            rows += 1
            counts[kind] += 1
            devices[device_id][kind] += 1
            if kind == "MISSING_SEQUENCE":
                missing_sequences += int(event.get("missing_count", 0))
            if kind == "RECOVERED" and "downtime_seconds" in event:
                recovery_seconds.append(float(event["downtime_seconds"]))
    return {
        "source": str(events_path),
        "total_events": rows,
        "event_counts": dict(sorted(counts.items())),
        "device_event_counts": {k: dict(sorted(v.items())) for k, v in sorted(devices.items())},
        "observed_sequence_gaps": missing_sequences,
        "recorded_recoveries": len(recovery_seconds),
        "mean_detected_downtime_seconds": (
            round(sum(recovery_seconds) / len(recovery_seconds), 4)
            if recovery_seconds else None
        ),
        "measurement_note": (
            "Sequence gaps reflect application sequence observations, not proven radio packet loss. "
            "Downtime is local monotonic elapsed time between first observed timeout and recovery."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FieldOps diagnostic JSON report")
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = summarize(args.events)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
