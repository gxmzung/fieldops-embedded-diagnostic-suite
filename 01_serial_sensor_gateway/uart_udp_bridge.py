"""Line-oriented UART to UDP bridge. Uses stdlib termios on POSIX systems."""
import argparse
import errno
import json
import os
import select
import signal
import socket
import sys
import termios
import time
import tty
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "03_field_telemetry_monitor"))
from parser import parse_sensor_line, SensorParseError
from health_checker import validate_telemetry

STOP = False


def _stop(*_args):
    global STOP
    STOP = True


def bridge(device: str, host: str = "127.0.0.1", port: int = 9000,
           baud: int = 115200, gps_fix: bool = False,
           max_frames: int = None, idle_limit: float = None) -> int:
    """Read newline-delimited FDU records and send validated UDP JSON.

    The requested baud rate is configured for serial devices using termios.
    A PTY is configured to raw mode; its nominal baud rate is not a physical clock.
    """
    if baud not in (9600, 19200, 38400, 57600, 115200):
        raise ValueError("unsupported baud rate")
    if not 1 <= port <= 65535:
        raise ValueError("invalid destination port")
    if max_frames is not None and max_frames <= 0:
        raise ValueError("max_frames must be positive")
    if idle_limit is not None and idle_limit <= 0:
        raise ValueError("idle_limit must be positive")
    speeds = {9600: termios.B9600, 19200: termios.B19200,
              38400: termios.B38400, 57600: termios.B57600,
              115200: termios.B115200}
    fd = os.open(device, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
    sent = 0
    buf = bytearray()
    last_input = time.monotonic()
    try:
        tty.setraw(fd)
        settings = termios.tcgetattr(fd)
        settings[4], settings[5] = speeds[baud], speeds[baud]
        termios.tcsetattr(fd, termios.TCSANOW, settings)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            print(f"UART bridge ready: {device} -> udp://{host}:{port}", flush=True)
            while not STOP:
                if idle_limit is not None and time.monotonic() - last_input >= idle_limit:
                    print("[UART] idle limit reached", flush=True)
                    break
                readable, _, _ = select.select([fd], [], [], 0.1)
                if not readable:
                    continue
                try:
                    chunk = os.read(fd, 4096)
                except BlockingIOError:
                    continue
                except OSError as exc:
                    if exc.errno in (errno.EIO, errno.ENXIO):
                        print("[UART] device disconnected", flush=True)
                        break
                    raise
                if not chunk:
                    print("[UART] EOF", flush=True)
                    break
                last_input = time.monotonic()
                buf.extend(chunk)
                if len(buf) > 8192:
                    print("[REJECTED] UART input buffer overflow", flush=True)
                    buf.clear()
                while b"\n" in buf:
                    raw, _, remainder = buf.partition(b"\n")
                    buf = bytearray(remainder)
                    try:
                        line = raw.decode("ascii").strip()
                        record = parse_sensor_line(line)
                        payload = {
                            "protocol_version": 1,
                            "sequence_number": sent,
                            "device_id": record.device_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "temperature_c": record.temperature_c,
                            "voltage_v": record.voltage_v,
                            "current_a": record.current_a,
                            # UART source has no GNSS field. Default False is conservative.
                            # --assume-gps-fix is only for explicitly simulated demos.
                            "gps_fix": gps_fix,
                        }
                        validate_telemetry(payload)
                    except (SensorParseError, UnicodeError, ValueError) as exc:
                        print(f"[REJECTED] UART record: {exc}", flush=True)
                        continue
                    sock.sendto(json.dumps(payload).encode("utf-8"), (host, port))
                    sent += 1
                    print(f"[UART->UDP] device={record.device_id} seq={sent-1}", flush=True)
                    if max_frames is not None and sent >= max_frames:
                        return sent
    finally:
        os.close(fd)
    return sent


def main():
    parser = argparse.ArgumentParser(description="POSIX UART/PTY sensor gateway to UDP")
    parser.add_argument("--device", required=True, help="e.g. /dev/cu.usbserial-xxxx")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--idle-limit", type=float)
    parser.add_argument("--assume-gps-fix", action="store_true",
                        help="Synthetic flag ONLY; not proof of GNSS fix")
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    try:
        bridge(args.device, args.host, args.port, args.baud,
               args.assume_gps_fix, args.max_frames, args.idle_limit)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"UART bridge error: {exc}\n")


if __name__ == "__main__":
    main()
