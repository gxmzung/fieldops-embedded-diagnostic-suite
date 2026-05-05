# Protocol Specification

## UART-like Sensor Message

```txt
FDU01,TEMP=42.3,VOLT=11.8,CURR=1.2,STATUS=OK
```

### Fields

| Field | Type | Normal Range |
|---|---:|---|
| Device ID | string | `FDU01` |
| TEMP | float | `< 70.0 °C` |
| VOLT | float | `>= 10.5 V` |
| CURR | float | `0.0 ~ 5.0 A` |
| STATUS | enum | `OK`, `WARN`, `FAULT` |

## Telemetry JSON

```json
{
  "device_id": "FDU01",
  "timestamp": "2026-05-05T12:00:00",
  "temperature_c": 43.2,
  "voltage_v": 11.7,
  "current_a": 1.4,
  "lat": 36.4812,
  "lon": 127.2891,
  "gps_fix": true
}
```

## Health Classification

| Health | Condition |
|---|---|
| NORMAL | All values inside operating range |
| WARN | Battery low or temperature elevated |
| CRITICAL | Overheat, critical voltage, GPS lost |
| LOST | No telemetry received for timeout period |
