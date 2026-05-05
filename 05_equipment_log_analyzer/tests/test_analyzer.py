import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer import extract_faults

def test_extract_faults():
    rows = [
        {"timestamp":"t1", "health":"NORMAL", "message":"ok"},
        {"timestamp":"t2", "health":"WARN", "message":"battery low"},
        {"timestamp":"t3", "health":"CRITICAL", "message":"gps lost"},
    ]
    faults = extract_faults(rows)
    assert len(faults) == 2
