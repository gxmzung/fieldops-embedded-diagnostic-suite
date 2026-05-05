import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parser import parse_sensor_line, classify_sensor, SensorParseError

def test_parse_ok():
    r = parse_sensor_line("FDU01,TEMP=42.3,VOLT=11.8,CURR=1.2,STATUS=OK")
    assert r.device_id == "FDU01"
    assert r.temperature_c == 42.3
    assert classify_sensor(r) == "NORMAL"

def test_parse_corrupted():
    try:
        parse_sensor_line("CORRUPTED")
        assert False
    except SensorParseError:
        assert True

def test_classify_critical():
    r = parse_sensor_line("FDU01,TEMP=90,VOLT=11.8,CURR=1.2,STATUS=OK")
    assert classify_sensor(r) == "CRITICAL"
