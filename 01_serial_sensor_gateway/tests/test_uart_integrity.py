import json
import os
import pty
import select
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "01_serial_sensor_gateway"))
from parser import LineFramer, SensorParseError, append_crc32, parse_sensor_line

A = "FDU01,TEMP=42.3,VOLT=11.8,CURR=1.2,STATUS=OK"
B = "FDU02,TEMP=43.0,VOLT=12.0,CURR=1.1,STATUS=OK"


def test_crc32_roundtrip_and_corruption():
    signed = append_crc32(A)
    assert parse_sensor_line(signed, require_crc=True).device_id == "FDU01"
    assert parse_sensor_line(A).device_id == "FDU01"  # legacy supported
    with pytest.raises(SensorParseError, match="required"):
        parse_sensor_line(A, require_crc=True)
    with pytest.raises(SensorParseError, match="mismatch"):
        parse_sensor_line(signed.replace("42.3", "42.4"), require_crc=True)


@pytest.mark.parametrize("line", [
    "FDU01,TEMP=nan,VOLT=11,CURR=1,STATUS=OK",
    "FDU01,TEMP=inf,VOLT=11,CURR=1,STATUS=OK",
    "FDU01,TEMP=42,VOLT=-1,CURR=1,STATUS=OK",
    "FDU01,TEMP=42,TEMP=43,CURR=1,STATUS=OK",
    "FDU01,TEMP=42,VOLT=11,CURR=1,STATUS=OK,EXTRA=1",
    "FDU01,TEMP=42,VOLT=11,CURR=1,STATUS=UNKNOWN",
    "bad id,TEMP=42,VOLT=11,CURR=1,STATUS=OK",
    "FDU01,TEMP=42,VOLT=11,CURR=1,STATUS=OK*abc",
])
def test_reject_malformed_uart(line):
    with pytest.raises(SensorParseError):
        parse_sensor_line(line)


def test_framer_resynchronizes_across_chunks():
    framer = LineFramer(512)
    assert list(framer.feed(b"partial")) == []
    assert list(framer.feed(b"\n")) == [(b"partial", None)]
    result = list(framer.feed(b"X" * 513 + b"\n" + A.encode() + b"\n"))
    assert result == [(None, "UART frame too long"), (A.encode(), None)]


@pytest.mark.skipif(sys.platform == "win32", reason="requires POSIX PTY")
def test_multi_device_bridge_isolates_bad_frames(tmp_path):
    master, slave = pty.openpty()
    device = os.ttyname(slave)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        receiver.bind(("127.0.0.1", 0))
        receiver.settimeout(3)
        port = receiver.getsockname()[1]
        cmd = [sys.executable, "-u", str(ROOT / "01_serial_sensor_gateway" / "uart_udp_bridge.py"),
               "--device", device, "--port", str(port), "--require-crc",
               "--assume-gps-fix", "--max-frames", "3"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            ready, _, _ = select.select([process.stdout], [], [], 3)
            assert ready, "bridge did not become ready"
            assert "bridge ready" in process.stdout.readline()
            payload = (
                append_crc32(A) + "\n"
                + append_crc32(B).replace("43.0", "43.1") + "\n"  # CRC corrupted
                + "X" * 600 + "\n"  # oversized frame
                + append_crc32(B) + "\n"
                + A + "\n"  # CRC missing
                + append_crc32(A) + "\n"
            ).encode("ascii")
            os.write(master, payload)
            packets = [json.loads(receiver.recvfrom(4096)[0]) for _ in range(3)]
            stdout, stderr = process.communicate(timeout=4)
            assert process.returncode == 0, stderr
            assert [(p["device_id"], p["sequence_number"]) for p in packets] == [
                ("FDU01", 0), ("FDU02", 0), ("FDU01", 1),
            ]
            assert all(p["gps_fix"] is True for p in packets)
            assert "[REJECTED]" in stdout
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
            os.close(master)
            os.close(slave)
