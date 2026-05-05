# FieldOps Embedded Diagnostic Suite

FieldOps Embedded Diagnostic Suite is a field-oriented embedded systems portfolio that simulates device telemetry, serial sensor acquisition, GNSS tracking, periodic task scheduling, and operational log analysis.

## Purpose

This project is designed to show an embedded / defense / aerospace-oriented workflow:

1. A field device generates sensor, telemetry, and GNSS data.
2. A gateway parses and validates incoming equipment data.
3. A monitor receives telemetry and classifies device health.
4. A task scheduler demonstrates periodic embedded-style execution.
5. A log analyzer produces a fault report from operational logs.

This is not a web/app portfolio. It is focused on **field equipment data, communication, validation, diagnostics, and operational logs**.

## Modules

| Module | Description |
|---|---|
| `simulator/` | Generates FDU-01 sample data |
| `01_serial_sensor_gateway/` | Parses UART-like sensor messages |
| `02_gnss_position_tracker/` | Parses NMEA `$GPRMC` GPS/GNSS data |
| `03_field_telemetry_monitor/` | Receives telemetry over UDP and detects faults |
| `04_embedded_task_scheduler/` | C-based periodic task scheduler with watchdog concept |
| `05_equipment_log_analyzer/` | Analyzes logs and generates Markdown fault reports |
| `docs/` | Field scenario, protocol spec, architecture, fault cases, interview summary |

## Quick Start

```bash
python3 scripts/generate_sample_data.py
python3 01_serial_sensor_gateway/gateway.py --input data/sensor_uart.txt --output data/sensor_log.csv
python3 02_gnss_position_tracker/tracker.py --input data/sample_nmea.txt --output data/position_log.csv
python3 05_equipment_log_analyzer/analyzer.py --input data/equipment_events.csv --report 05_equipment_log_analyzer/reports/fault_report.md
```

### Telemetry Monitor Demo

Terminal 1:

```bash
python3 03_field_telemetry_monitor/telemetry_server.py --host 127.0.0.1 --port 9000 --output data/telemetry_events.csv
```

Terminal 2:

```bash
python3 simulator/fdu_device_simulator.py --udp-host 127.0.0.1 --udp-port 9000 --count 30
```

### C Scheduler

```bash
cd 04_embedded_task_scheduler
make
./scheduler_demo
```

## What this project demonstrates

- UART-like equipment data parsing
- GNSS NMEA parsing
- UDP telemetry reception
- Health state classification: `NORMAL`, `WARN`, `CRITICAL`, `LOST`
- Embedded-style periodic task execution in C
- Fault event extraction and report generation
- Practical documentation for field equipment operation

## Interview Summary

> I built this project to understand how field equipment data is collected, monitored, diagnosed, and analyzed in embedded, defense, and aerospace environments. The project includes UART-like sensor parsing, GNSS tracking, telemetry monitoring, embedded task scheduling, and fault log analysis.
