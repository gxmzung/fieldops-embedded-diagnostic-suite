from collections import Counter

def build_markdown_report(rows: list[dict], faults: list[dict]) -> str:
    health_counts = Counter(row.get("health", "UNKNOWN") for row in rows)
    device_id = rows[0].get("device_id", "UNKNOWN") if rows else "UNKNOWN"

    lines = [
        "# FDU-01 Fault Report",
        "",
        "## Summary",
        f"- Device: {device_id}",
        f"- Total Events: {len(rows)}",
        f"- NORMAL: {health_counts.get('NORMAL', 0)}",
        f"- WARN: {health_counts.get('WARN', 0)}",
        f"- CRITICAL: {health_counts.get('CRITICAL', 0)}",
        "",
        "## Detected Fault Timeline",
    ]

    if not faults:
        lines.append("- No warning or critical events detected.")
    else:
        for idx, fault in enumerate(faults, 1):
            lines.append(f"{idx}. {fault['timestamp']} - [{fault['health']}] {fault['message']}")

    lines.extend([
        "",
        "## Possible Cause",
        infer_possible_cause(faults),
        "",
        "## Recommended Follow-up",
        "- Check battery condition and load profile.",
        "- Review thermal environment and cooling path.",
        "- Verify GNSS antenna placement and cable connection.",
        "- Compare telemetry timeout pattern with communication logs.",
    ])

    return "\n".join(lines) + "\n"

def infer_possible_cause(faults: list[dict]) -> str:
    messages = " ".join(f.get("message", "").lower() for f in faults)
    if "battery" in messages and "temperature" in messages:
        return "Battery degradation or high-load operation may have caused voltage drop and temperature increase."
    if "gps" in messages:
        return "GNSS receiver signal loss or antenna/cable issue may have occurred."
    if "temperature" in messages:
        return "High thermal load or insufficient cooling may have caused elevated temperature."
    if "battery" in messages:
        return "Battery voltage drop may indicate discharge, degradation, or excessive current draw."
    return "No specific cause inferred from available logs."
