"""Per-device communication state for UDP telemetry diagnostics.

The receiver uses a monotonic clock for local timeout decisions. Sequence
numbers are optional for compatibility with legacy, unversioned packets.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceState:
    last_seen: float
    last_sequence: Optional[int] = None
    lost: bool = False
    missing_sequence_count: int = 0
    duplicate_count: int = 0
    out_of_order_count: int = 0


class DiagnosticTracker:
    def __init__(self, timeout_seconds: float = 5.0):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self.devices: dict[str, DeviceState] = {}

    def observe(self, device_id: str, received_at: float, sequence_number=None) -> list[str]:
        state = self.devices.get(device_id)
        if state is None:
            self.devices[device_id] = DeviceState(received_at, sequence_number)
            return ["CONNECTED"]
        events = []
        if state.lost:
            events.append("RECOVERED")
        state.last_seen = received_at
        state.lost = False
        if sequence_number is None:
            return events
        if state.last_sequence is None:
            state.last_sequence = sequence_number
            return events
        # Assumes 32-bit unsigned sequence values; large backward movements
        # are treated as older packets, not as forward gaps.
        delta = (sequence_number - state.last_sequence) % (2 ** 32)
        if delta == 0:
            state.duplicate_count += 1
            events.append("DUPLICATE")
        elif delta < 2 ** 31:
            if delta > 1:
                state.missing_sequence_count += delta - 1
                events.append(f"MISSING_SEQUENCE:{delta - 1}")
            state.last_sequence = sequence_number
        else:
            state.out_of_order_count += 1
            events.append("OUT_OF_ORDER")
        return events

    def check_timeouts(self, now: float) -> list[str]:
        lost = []
        for device_id, state in self.devices.items():
            if not state.lost and now - state.last_seen >= self.timeout_seconds:
                state.lost = True
                lost.append(device_id)
        return lost
