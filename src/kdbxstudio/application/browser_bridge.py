"""KeePassXC-Browser-shaped protocol helpers and local socket bridge.

Full NaCl association + browser extension shipping is Phase 0 follow-up.
This module provides:
- database hash for association checks
- get-logins matching by URL host
- a Unix socket server the native messaging host can talk to
"""

from __future__ import annotations

import hashlib
import json
import socket
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from kdbxstudio.core.database import EntryView
from kdbxstudio.core.paths import default_data_dir


def browser_socket_path() -> Path:
    root = default_data_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root / "browser.sock"


def database_hash(path: Path | str | None, password_hint: str = "") -> str:
    """Stable opaque id for an unlocked vault (not the master password)."""
    material = f"{path or 'memory'}|{password_hint}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def url_host(url: str) -> str:
    text = (url or "").strip()
    if not text:
        return ""
    if "://" not in text:
        text = "https://" + text
    try:
        host = (urlparse(text).hostname or "").lower()
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def match_logins_for_url(entries: list[EntryView], url: str) -> list[EntryView]:
    host = url_host(url)
    if not host:
        return []
    hits: list[EntryView] = []
    for entry in entries:
        if entry.in_recycle_bin:
            continue
        entry_host = url_host(entry.url)
        if not entry_host:
            continue
        if entry_host == host or host.endswith("." + entry_host) or entry_host.endswith(
            "." + host
        ):
            hits.append(entry)
    return hits


@dataclass
class BrowserVaultSnapshot:
    database_hash: str
    entries: list[EntryView]


LoginProvider = Callable[[], BrowserVaultSnapshot | None]


class BrowserBridgeServer:
    """Tiny JSON line protocol over a Unix domain socket."""

    def __init__(self, provider: LoginProvider) -> None:
        self._provider = provider
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._sock: socket.socket | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> Path:
        path = browser_socket_path()
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        self._stop.clear()
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(str(path))
        self._sock.listen(5)
        self._sock.settimeout(1.0)
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        return path

    def stop(self) -> None:
        self._stop.set()
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        path = browser_socket_path()
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass

    def _serve(self) -> None:
        assert self._sock is not None
        while not self._stop.is_set():
            try:
                conn, _addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with conn:
                self._handle(conn)

    def _handle(self, conn: socket.socket) -> None:
        buffer = b""
        while not self._stop.is_set():
            chunk = conn.recv(65536)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    request = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    conn.sendall(
                        b'{"success":false,"error":"invalid json"}\n'
                    )
                    continue
                response = self.handle_request(request)
                conn.sendall((json.dumps(response) + "\n").encode("utf-8"))

    def handle_request(self, request: dict) -> dict:
        action = str(request.get("action") or "")
        if action == "ping":
            return {"success": True, "version": "1.0.0"}
        snapshot = self._provider()
        if snapshot is None:
            return {"success": False, "error": "database-locked"}
        if action == "get-databasehash":
            return {"success": True, "hash": snapshot.database_hash}
        if action == "get-logins":
            url = str(request.get("url") or "")
            hits = match_logins_for_url(snapshot.entries, url)
            return {
                "success": True,
                "entries": [
                    {
                        "uuid": e.uuid,
                        "name": e.title,
                        "login": e.username,
                        "password": e.password,
                        "otp": e.otp,
                        "url": e.url,
                    }
                    for e in hits
                ],
            }
        return {"success": False, "error": f"unknown-action:{action}"}


def request_bridge(action: str, **payload: object) -> dict:
    """Client helper used by the native messaging host."""
    path = browser_socket_path()
    if not path.exists():
        return {"success": False, "error": "bridge-not-running"}
    message = {"action": action, **payload}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(3)
        sock.connect(str(path))
        sock.sendall((json.dumps(message) + "\n").encode("utf-8"))
        data = b""
        while b"\n" not in data:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
    if not data:
        return {"success": False, "error": "empty-response"}
    line = data.split(b"\n", 1)[0]
    return json.loads(line.decode("utf-8"))
