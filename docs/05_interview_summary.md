# Interview Summary

## Project Positioning

This is a field-oriented embedded systems portfolio, not a web/app project.

## One-minute Explanation

I built a simulated field equipment diagnostic suite to understand how embedded devices are monitored and diagnosed in field environments. The system includes UART-like sensor parsing, GNSS NMEA parsing, telemetry monitoring, C-based task scheduling, and fault log analysis. I focused on data validation, fault classification, operational logs, and documentation rather than only making a simple demo.

## What I learned

- How equipment data can be defined as a protocol.
- How malformed data and fault states should be handled.
- How telemetry and logs support field diagnostics.
- Why documentation and test cases matter in equipment-oriented development.

## Honest Limitation

This project uses simulated data rather than actual hardware. The next step would be connecting it to a real MCU, GPS module, or serial sensor.
