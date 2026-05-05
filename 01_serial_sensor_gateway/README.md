# Serial Sensor Gateway

Parses UART-like sensor messages from the simulated FDU-01 field device.

## Run

```bash
python3 01_serial_sensor_gateway/gateway.py --input data/sensor_uart.txt --output data/sensor_log.csv
```

## What it detects

- Malformed lines
- Invalid numeric values
- Low voltage
- Over temperature
- Non-OK status
