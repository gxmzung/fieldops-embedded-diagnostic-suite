import argparse
import csv
from pathlib import Path
from report_generator import build_markdown_report

def read_rows(input_path: Path) -> list[dict]:
    with input_path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def extract_faults(rows: list[dict]) -> list[dict]:
    faults = []
    for row in rows:
        health = row.get("health", "").upper()
        if health in ("WARN", "CRITICAL", "LOST"):
            faults.append({
                "timestamp": row.get("timestamp", ""),
                "health": health,
                "message": row.get("message", "")
            })
    return faults

def analyze(input_path: Path, report_path: Path) -> tuple[int, int]:
    rows = read_rows(input_path)
    faults = extract_faults(rows)
    report = build_markdown_report(rows, faults)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return len(rows), len(faults)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Equipment log analyzer")
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    total, faults = analyze(Path(args.input), Path(args.report))
    print(f"events={total}, faults={faults}, report={args.report}")
