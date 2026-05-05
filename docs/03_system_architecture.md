# System Architecture

```txt
+-----------------------+
| FDU Device Simulator  |
+-----------+-----------+
            |
            | UART-like sensor data / NMEA / UDP telemetry
            v
+-----------------------+      +----------------------+
| Serial Sensor Gateway |      | GNSS Position Tracker|
+-----------+-----------+      +----------+-----------+
            |                             |
            v                             v
+-----------------------------------------------------+
|               Field Telemetry Monitor               |
|        Health check / event log / dashboard         |
+--------------------------+--------------------------+
                           |
                           v
+-----------------------------------------------------+
|              Equipment Log Analyzer                 |
|        Fault extraction / timeline / report         |
+-----------------------------------------------------+
```

## Design Intent

The suite separates acquisition, monitoring, scheduling, and analysis to reflect how field systems are often structured in practice.
