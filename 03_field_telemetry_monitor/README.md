# Field Telemetry Monitor

Receives FDU-01 telemetry over UDP and classifies equipment health.

## Run

Terminal 1:

```bash
python3 03_field_telemetry_monitor/telemetry_server.py --host 127.0.0.1 --port 9000 --output data/telemetry_events.csv
```

Terminal 2:

```bash
python3 simulator/fdu_device_simulator.py --udp-host 127.0.0.1 --udp-port 9000 --count 30
```
