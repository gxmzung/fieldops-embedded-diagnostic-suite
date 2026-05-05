import argparse
import csv
import math
from pathlib import Path
from nmea_parser import parse_gprmc, NmeaParseError

def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1-a))

def track_file(input_path: Path, output_path: Path) -> tuple[int, int, float]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid_count = 0
    invalid_count = 0
    total_distance = 0.0
    prev = None

    with input_path.open("r", encoding="utf-8") as src, output_path.open("w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=[
            "time_utc", "valid", "latitude", "longitude", "speed_knots", "distance_from_prev_m"
        ])
        writer.writeheader()

        for line in src:
            try:
                rec = parse_gprmc(line)
                distance = 0.0
                if rec.valid and prev is not None:
                    distance = haversine_m(prev[0], prev[1], rec.latitude, rec.longitude)
                    total_distance += distance
                if rec.valid:
                    prev = (rec.latitude, rec.longitude)
                    valid_count += 1
                else:
                    invalid_count += 1
                writer.writerow({
                    "time_utc": rec.time_utc,
                    "valid": rec.valid,
                    "latitude": rec.latitude,
                    "longitude": rec.longitude,
                    "speed_knots": rec.speed_knots,
                    "distance_from_prev_m": round(distance, 2)
                })
            except NmeaParseError:
                invalid_count += 1

    return valid_count, invalid_count, total_distance

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GNSS NMEA position tracker")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    valid, invalid, distance = track_file(Path(args.input), Path(args.output))
    print(f"valid_fix={valid}, invalid_or_no_fix={invalid}, total_distance_m={distance:.2f}")
