import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nmea_parser import parse_gprmc

def test_parse_valid_gprmc():
    s = "$GPRMC,120000,A,3628.8000,N,12717.4000,E,10.0,084.4,050526,,,A*6A"
    r = parse_gprmc(s)
    assert r.valid is True
    assert r.latitude is not None
    assert r.longitude is not None
