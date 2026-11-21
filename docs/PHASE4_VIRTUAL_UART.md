# Phase 4 — Hardware-free UART interface validation

No ESP32, sensor, or USB-UART adapter is required for this phase.

## Run on macOS (or Linux)

```bash
cd ~/dev/fieldops-embedded-diagnostic-suite
source .venv/bin/activate
python tools/run_virtual_uart_experiment.py
python -m pytest -q
```

The runner opens a POSIX pseudo-terminal (PTY), starts the real UART-to-UDP
bridge and existing UDP telemetry receiver, injects two ASCII sensor frames,
pauses frame transmission until the receiver detects LOST, then sends a third
frame to trigger RECOVERED. Results are saved under `out/virtual-uart/<run-id>/`.

Expected diagnostic events: TELEMETRY=3, CONNECTED=1, LOST=1, RECOVERED=1.
The runner exits nonzero if these invariants are not satisfied.

Line protocol: one ASCII record per newline, e.g.

```text
FDU01,TEMP=42.3,VOLT=11.8,CURR=1.2,STATUS=OK
```

## When a real serial adapter becomes available

First check the path (e.g. `ls /dev/cu.*` on macOS), serial baud configuration,
and actual device frame format. Start UDP receiver separately and run:

```bash
python 01_serial_sensor_gateway/uart_udp_bridge.py \
  --device /dev/cu.usbserial-XXXX --baud 115200
```

Replace device path with the actual detected device. Frames are sent to
127.0.0.1:9000 by default.

## Non-negotiable limits

- PTY is a **software virtual serial interface**, not USB hardware or an MCU.
- Pausing the PTY writer is **application-level silence**. It does not test
  physical plug/unplug, kernel device removal, or reconnection to a new port.
- The existing UART line format has no GNSS-fix field. The bridge defaults
  to `gps_fix=false` conservatively; `--assume-gps-fix` is a **synthetic
  demo flag** and must never be used to claim measured GNSS availability.
- Existing sequence numbers are assigned by the *bridge*, not by the MCU.
  Link-level losses **upstream** of the bridge cannot be inferred from these
  numbers. UART framing/integrity and byte loss remain unverified.
- This validates a software interface boundary on local macOS/Linux only;
  it is not a hardware-in-the-loop or field acceptance test.
