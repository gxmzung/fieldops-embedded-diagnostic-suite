import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from diagnostic_state import DiagnosticTracker
from health_checker import classify_telemetry, validate_telemetry
import pytest


BASE = {
    "device_id": "FDU01", "temperature_c": 42.0,
    "voltage_v": 12.0, "current_a": 1.0, "gps_fix": True,
}


@pytest.mark.parametrize("field,value", [
    ("gps_fix", "false"), ("gps_fix", 1),
    ("temperature_c", float("nan")), ("voltage_v", float("inf")),
    ("current_a", -1), ("device_id", ""), ("protocol_version", 2),
    ("sequence_number", -1), ("sequence_number", True),
    ("lat", 100), ("lon", -190),
])
def test_invalid_types_and_ranges(field, value):
    with pytest.raises(ValueError):
        validate_telemetry({**BASE, field: value})


def test_invalid_boolean_cannot_appear_nominal():
    result = classify_telemetry({**BASE, "gps_fix": "false"})
    assert result.health == "CRITICAL"
    assert "invalid telemetry" in result.message


def test_legacy_packet_accepted():
    assert validate_telemetry(BASE) == BASE


def test_versioned_packet_accepted():
    p = {**BASE, "protocol_version": 1, "sequence_number": 123}
    assert validate_telemetry(p) == p


def test_timeout_once_and_recovery():
    tracker = DiagnosticTracker(timeout_seconds=5)
    assert tracker.observe("A", 10.0) == ["CONNECTED"]
    assert tracker.check_timeouts(14.9) == []
    assert tracker.check_timeouts(15.0) == ["A"]
    assert tracker.check_timeouts(20.0) == []
    assert tracker.observe("A", 21.0) == ["RECOVERED"]
    assert tracker.check_timeouts(25.9) == []


def test_sequence_missing_duplicate_and_out_of_order():
    tracker = DiagnosticTracker()
    assert tracker.observe("A", 1, 5) == ["CONNECTED"]
    assert tracker.observe("A", 2, 8) == ["MISSING_SEQUENCE:2"]
    assert tracker.observe("A", 3, 8) == ["DUPLICATE"]
    assert tracker.observe("A", 4, 7) == ["OUT_OF_ORDER"]
    state = tracker.devices["A"]
    assert (state.missing_sequence_count, state.duplicate_count,
            state.out_of_order_count) == (2, 1, 1)


def test_sequence_wraparound():
    tracker = DiagnosticTracker()
    tracker.observe("A", 1, 4294967295)
    assert tracker.observe("A", 2, 0) == []


def test_invalid_timeout():
    with pytest.raises(ValueError):
        DiagnosticTracker(0)
