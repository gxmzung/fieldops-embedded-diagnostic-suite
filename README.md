# FieldOps Embedded Diagnostic Suite

임베디드 장비 **FDU-01**을 가정하고  
**센서 데이터 수집 → 통신 → 관제 → 로그 분석 → 웹 시각화**까지 구현한 프로젝트입니다.

---

## 🔧 System Overview

```txt
[Sensor UART]
    ↓
[Serial Gateway]
    ↓
[Telemetry UDP]
    ↓
[Monitoring Server]
    ↓
[CSV Logging]
    ↓
[Web Dashboard]
    ↓
[Fault Analysis Report]
```

---

## 🧠 Architecture

### 01_serial_sensor_gateway
- UART 데이터 파싱
- 센서 상태 분류: `NORMAL`, `WARN`, `CRITICAL`

### 02_gnss_position_tracker
- NMEA 데이터 파싱
- 위치 추적 및 거리 계산

### 03_field_telemetry_monitor
- UDP 기반 관제 서버
- 온도, 전압, GPS 상태 기반 이상 감지

### 04_embedded_task_scheduler
- C 기반 주기적 태스크 실행
- 센서 읽기, 전송, 헬스체크, 로그 저장 흐름 구현

### 05_equipment_log_analyzer
- 장애 로그 분석
- Fault Report 생성

### 06_web_dashboard
- Chart.js 기반 실시간 데이터 시각화
- 장비 상태 대시보드

---

## 📊 Web Dashboard

### Run

```bash
python3 06_web_dashboard/dashboard.py
```

Open:

```txt
http://127.0.0.1:8080/06_web_dashboard/
```

### Features

- 실시간 온도 / 전압 그래프
- 장비 상태 표시: `NORMAL`, `WARN`, `CRITICAL`
- GPS 상태 감지: `fix lost`
- 이벤트 로그 테이블

---

## ⚠️ Fault Scenarios

| Condition | Status |
|---|---|
| Temperature > 85°C | `CRITICAL temperature` |
| Voltage < 10V | `CRITICAL battery` |
| GPS fix false | `CRITICAL gps lost` |

---

## 📁 Example Output

### Telemetry CSV

```csv
device_id,timestamp,temperature_c,voltage_v,gps_fix,health,message
FDU01,2026-05-05T08:13:28,44.44,11.23,True,NORMAL,nominal
FDU01,2026-05-05T08:13:27,49.48,11.32,False,CRITICAL,gps fix lost
```

### Fault Report

```md
Total events: 80
Detected faults: 14

- temperature critical
- battery critical
- gps fix lost
```

---

## 🚀 How to Run

### 1. Generate Sample Data

```bash
python3 scripts/generate_sample_data.py
```

### 2. Serial Sensor Gateway

```bash
python3 01_serial_sensor_gateway/gateway.py --input data/sensor_uart.txt --output data/sensor_log.csv
```

### 3. GNSS Position Tracker

```bash
python3 02_gnss_position_tracker/tracker.py --input data/sample_nmea.txt --output data/position_log.csv
```

### 4. Equipment Log Analyzer

```bash
python3 05_equipment_log_analyzer/analyzer.py --input data/equipment_events.csv --report 05_equipment_log_analyzer/reports/fault_report.md
```

### 5. Telemetry Monitor

Terminal 1:

```bash
python3 03_field_telemetry_monitor/telemetry_server.py --host 127.0.0.1 --port 9000 --output data/telemetry_events.csv
```

Terminal 2:

```bash
python3 simulator/fdu_device_simulator.py --udp-host 127.0.0.1 --udp-port 9000 --count 30
```

### 6. Embedded Task Scheduler

```bash
cd 04_embedded_task_scheduler
make
./scheduler_demo
cd ..
```

### 7. Web Dashboard

```bash
python3 06_web_dashboard/dashboard.py
```

---

## 🎯 Purpose

이 프로젝트는 단순 앱 개발이 아니라,  
**현장 장비 운용 흐름을 이해하기 위한 임베디드 / 관제 시스템 설계**를 목표로 했습니다.

---

## 🧩 Key Points

- UART / UDP 기반 데이터 흐름 구현
- 센서 이상 탐지 로직 구현
- GNSS 위치 추적 및 거리 계산
- 실시간 관제 시스템 구조 구현
- C 기반 태스크 스케줄링 구현
- 데이터 수집부터 웹 시각화까지 End-to-End 구현

---

## 📌 Summary

> 임베디드 장비 데이터를 수집하고, 이상 상태를 감지하며, 관제 시스템으로 시각화하는 전체 흐름을 구현한 프로젝트입니다.
