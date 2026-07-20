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
import secrets
import socket
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

_MAX_BUFFER_BYTES = 1 * 1024 * 1024  # 1 MiB

from kdbxstudio.core.database import EntryView  # noqa: E402
from kdbxstudio.core.paths import default_data_dir, ensure_private_dir  # noqa: E402


def browser_socket_path() -> Path:
    root = ensure_private_dir(default_data_dir())
    return root / "browser.sock"


def database_hash(path: Path | str | None, password_hint: str = "") -> str:
    """Stable opaque id for an unlocked vault (not the master password)."""
    material = f"{path or 'memory'}|{password_hint}".encode()
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
        # A credential scoped to ``accounts.example.com`` must not be offered
        # to the broader ``example.com`` origin.  The current page may be an
        # exact match or a subdomain of the stored entry, never the reverse.
        if entry_host == host or host.endswith("." + entry_host):
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
        self._auth_token: str = secrets.token_hex(32)
        self._authenticated: set[int] = set()

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
            except TimeoutError:
                continue
            except OSError:
                break
            with conn:
                self._handle(conn)

    def _handle(self, conn: socket.socket) -> None:
        authenticated = False
        buffer = b""
        while not self._stop.is_set():
            chunk = conn.recv(65536)
            if not chunk:
                break
            buffer += chunk
            if len(buffer) > _MAX_BUFFER_BYTES:
                conn.sendall(b'{"success":false,"error":"buffer overflow"}\n')
                break
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    request = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    conn.sendall(b'{"success":false,"error":"invalid json"}\n')
                    continue
                action = str(request.get("action") or "")
                if action == "ping":
                    resp = json.dumps({"success": True, "version": "1.0.0"})
                    conn.sendall((resp + "\n").encode())
                    continue
                if not authenticated:
                    token = str(request.get("token") or "")
                    if secrets.compare_digest(token, self._auth_token):
                        authenticated = True
                        resp = json.dumps({"success": True, "authenticated": True})
                        conn.sendall((resp + "\n").encode())
                    else:
                        conn.sendall(
                            b'{"success":false,"error":"authentication required"}\n'
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


def request_bridge(action: str, *, auth_token: str = "", **payload: object) -> dict:
    """Client helper used by the native messaging host."""
    path = browser_socket_path()
    if not path.exists():
        return {"success": False, "error": "bridge-not-running"}
    message = {"action": action, **payload}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(3)
        sock.connect(str(path))
        if auth_token:
            auth_msg = {"action": "authenticate", "token": auth_token}
            sock.sendall((json.dumps(auth_msg) + "\n").encode("utf-8"))
            data = b""
            while b"\n" not in data:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
            if not data:
                return {"success": False, "error": "auth-failed"}
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
