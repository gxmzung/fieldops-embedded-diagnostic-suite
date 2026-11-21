"""Repeatable UDP application-packet fault scenarios for FieldOps.

Loss, duplication and reordering here are injected at the sender application
layer. They are not measurements of radio-layer or real-network faults.
"""
import argparse
import json
import socket
import time
from pathlib import Path

from fdu_device_simulator import make_packet


def sequence_for_scenario(scenario: str, count: int) -> list[int]:
    if count < 5:
        raise ValueError("count must be >= 5 to exercise all fault scenarios")
    indices = list(range(count))
    if scenario == "normal":
        return indices
    if scenario == "drop":
        return [index for index in indices if index != 2]
    if scenario == "duplicate":
        indices.insert(4, 3)
        return indices
    if scenario == "reorder":
        indices[2], indices[3] = indices[3], indices[2]
        return indices
    if scenario == "mixed":
        # 0,1,3,3,2,4... -> gap, duplicate, out-of-order.
        return [0, 1, 3, 3, 2] + list(range(4, count))
    raise ValueError(f"unknown scenario: {scenario}")


def run_scenario(host: str, port: int, scenario: str, count: int,
                 interval: float, manifest: Path = None) -> dict:
    if not 0 <= port <= 65535:
        raise ValueError("invalid UDP port")
    if interval < 0:
        raise ValueError("interval must not be negative")
    indices = sequence_for_scenario(scenario, count)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for index in indices:
            packet = make_packet(index)
            packet["protocol_version"] = 1
            packet["sequence_number"] = index
            sock.sendto(json.dumps(packet, allow_nan=False).encode("utf-8"), (host, port))
            print(f"SENT scenario={scenario} sequence={index}")
            if interval:
                time.sleep(interval)
    result = {
        "scenario": scenario, "generated_sequence_count": count,
        "sent_datagrams": len(indices), "sent_sequences": indices,
        "fault_model": "sender application-layer injection",
    }
    if manifest is not None:
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject deterministic UDP telemetry faults")
    parser.add_argument("--udp-host", default="127.0.0.1")
    parser.add_argument("--udp-port", type=int, default=9000)
    parser.add_argument("--scenario", choices=["normal", "drop", "duplicate", "reorder", "mixed"],
                        default="mixed")
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--interval", type=float, default=0.05)
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()
    run_scenario(args.udp_host, args.udp_port, args.scenario,
                 args.count, args.interval, args.manifest)


if __name__ == "__main__":
    main()
