# Fault Cases

## Low Voltage

- Condition: `voltage_v < 10.5`
- Severity: WARN
- Critical condition: `voltage_v < 9.8`

## Over Temperature

- Condition: `temperature_c >= 70.0`
- Severity: WARN
- Critical condition: `temperature_c >= 85.0`

## GPS Loss

- Condition: `gps_fix == false`
- Severity: CRITICAL

## Telemetry Timeout

- Condition: no telemetry packet received during timeout window
- Severity: LOST

## Malformed Data

- Condition: required fields missing or cannot be parsed
- Severity: invalid input, logged or skipped
