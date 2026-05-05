import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from health_checker import classify_telemetry

def test_normal():
    r = classify_telemetry({"device_id":"FDU01","temperature_c":40,"voltage_v":12,"current_a":1,"gps_fix":True})
    assert r.health == "NORMAL"

def test_critical_temp():
    r = classify_telemetry({"device_id":"FDU01","temperature_c":90,"voltage_v":12,"current_a":1,"gps_fix":True})
    assert r.health == "CRITICAL"

def test_gps_lost():
    r = classify_telemetry({"device_id":"FDU01","temperature_c":40,"voltage_v":12,"current_a":1,"gps_fix":False})
    assert r.health == "CRITICAL"
