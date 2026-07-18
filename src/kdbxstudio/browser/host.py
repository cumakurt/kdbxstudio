"""Native messaging host / keepassxc-proxy compatible forwarder.

Reads length-prefixed JSON from the browser extension and forwards each
message to the KeePassXC-compatible Unix socket served by KDBXStudio.
"""

from __future__ import annotations

import json
import os
import socket
import struct
import sys
from pathlib import Path


def _socket_candidates() -> list[str]:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or str(Path.home() / ".cache")
    xdg_data = os.environ.get("XDG_DATA_HOME")
    data = Path(xdg_data) / "kdbxstudio" if xdg_data else Path.home() / ".local/share/kdbxstudio"
    return [
        str(Path(runtime) / "app/org.keepassxc.KeePassXC/org.keepassxc.KeePassXC.BrowserServer"),
        str(Path(runtime) / "org.keepassxc.KeePassXC.BrowserServer"),
        str(data / "browser.sock"),
    ]


def _connect() -> socket.socket:
    last_error: Exception | None = None
    for path in _socket_candidates():
        if not Path(path).exists() and not _is_socket(path):
            continue
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(5)
            sock.connect(path)
            return sock
        except OSError as exc:
            last_error = exc
            try:
                sock.close()
            except OSError:
                pass
    raise ConnectionError(str(last_error or "browser bridge socket not found"))


def _is_socket(path: str) -> bool:
    try:
        return Path(path).is_socket()
    except OSError:
        return False


def _read_native() -> dict | None:
    raw_len = sys.stdin.buffer.read(4)
    if not raw_len or len(raw_len) < 4:
        return None
    length = struct.unpack("<I", raw_len)[0]
    if length <= 0 or length > 1024 * 1024:
        return None
    data = sys.stdin.buffer.read(length)
    if not data:
        return None
    return json.loads(data.decode("utf-8"))


def _write_native(payload: dict) -> None:
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def _roundtrip(request: dict) -> dict:
    with _connect() as sock:
        sock.sendall(json.dumps(request, separators=(",", ":")).encode("utf-8"))
        chunks = b""
        while True:
            part = sock.recv(65536)
            if not part:
                break
            chunks += part
            # KeePassXC writes one JSON object per response; parse when valid.
            try:
                return json.loads(chunks.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
    return {
        "action": str(request.get("action") or ""),
        "errorCode": "5",
        "error": "Timeout or not connected",
    }


def main() -> int:
    while True:
        message = _read_native()
        if message is None:
            return 0
        try:
            response = _roundtrip(message)
        except Exception as exc:
            response = {
                "action": str(message.get("action") or ""),
                "errorCode": "5",
                "error": f"Timeout or not connected: {exc}",
            }
        _write_native(response)
