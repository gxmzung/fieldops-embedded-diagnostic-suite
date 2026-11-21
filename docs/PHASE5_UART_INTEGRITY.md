# Phase 5 — UART framing and multi-device integrity

No actual sensor hardware is required to validate the parser and PTY pipeline.

## New behavior
- Legacy ASCII frames remain accepted by default.
- Optional CRC32 suffix: `*XXXXXXXX` where `XXXXXXXX` is eight hexadecimal digits.
- CRC32 computed over the exact ASCII payload before the asterisk, using standard IEEE reflected CRC32 (`zlib.crc32`), excluding newline and suffix.
- Pass `--require-crc` to the UART bridge to **reject frames without** a valid CRC32 suffix.
- Invalid fields, non-finite/out-of-range measurements, unknown status values, malformed CRC and frames over 512 bytes are rejected.
- An oversized frame is discarded until the next newline; subsequent complete frames can be accepted.
- Sequence numbers assigned **by the bridge** advance independently per `device_id` and wrap at 2^32.

## Try on macOS

```bash
cd ~/dev/fieldops-embedded-diagnostic-suite
source .venv/bin/activate
python -m pytest -q
python tools/run_virtual_uart_experiment.py
```

To produce a signed sample frame locally:

```bash
python - <<'PY'
import sys
sys.path.insert(0, "01_serial_sensor_gateway")
from parser import append_crc32
print(append_crc32("FDU01,TEMP=42.3,VOLT=11.8,CURR=1.2,STATUS=OK"))
PY
```

To use a *real serial port in the future*, the source firmware must send this wire format with the matching CRC algorithm. The `--require-crc` flag cannot retrofit protection onto an existing firmware that does not send CRC.

## Boundaries and unresolved items
- CRC32 detects accidental line corruption but **does not provide cryptographic authenticity**.
- Bridge-generated sequence numbers **cannot detect dropped UART lines before the bridge**.
- The existing UART source format carries no GNSS state. `--assume-gps-fix` remains a synthetic demonstration flag.
- The `STATUS` field is validated but currently is not mapped to a distinct UDP health field. It is not an independently proven sensor-health check.
- Not tested: hardware unplug/re-enumeration, multiple serial ports, throughput limits, adversarial network input, or radio packet loss.
- This phase validates multiple logical device IDs on **one virtual serial stream**.
