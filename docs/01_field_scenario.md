# Field Scenario

## Device

**FDU-01 Field Diagnostic Unit**

FDU-01 is a simulated field device used in a defense/aerospace-style environment.
It periodically reports:

- Temperature
- Battery voltage
- Current draw
- Device status
- GNSS location
- Communication health

## Operational Flow

1. The device generates UART-like sensor messages.
2. GNSS receiver outputs NMEA messages.
3. Telemetry packets are sent to the monitoring station.
4. The monitoring station classifies the device health.
5. Logs are analyzed after operation to identify fault sequences.

## Fault Scenarios

- Battery voltage drops below threshold.
- Temperature exceeds safe operating range.
- GNSS fix is lost.
- Telemetry packet is delayed or missing.
- Malformed sensor data appears.
