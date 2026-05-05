import argparse
import csv
from pathlib import Path
from parser import parse_sensor_line, classify_sensor, SensorParseError

def process_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid = 0
    invalid = 0

    with input_path.open("r", encoding="utf-8") as src, output_path.open("w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=[
            "device_id", "temperature_c", "voltage_v", "current_a", "status", "health"
        ])
        writer.writeheader()

        for line in src:
            try:
                record = parse_sensor_line(line)
                health = classify_sensor(record)
                writer.writerow({
                    "device_id": record.device_id,
                    "temperature_c": record.temperature_c,
                    "voltage_v": record.voltage_v,
                    "current_a": record.current_a,
                    "status": record.status,
                    "health": health
                })
                valid += 1
            except SensorParseError:
                invalid += 1

    return valid, invalid

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UART-like sensor gateway")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    valid, invalid = process_file(Path(args.input), Path(args.output))
    print(f"valid={valid}, invalid={invalid}, output={args.output}")
