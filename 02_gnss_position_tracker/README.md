# GNSS Position Tracker

Parses `$GPRMC` NMEA sentences and tracks FDU-01 movement.

## Run

```bash
python3 02_gnss_position_tracker/tracker.py --input data/sample_nmea.txt --output data/position_log.csv
```

## Features

- Checksum validation
- GPS FIX detection
- Latitude/longitude conversion
- Distance calculation
