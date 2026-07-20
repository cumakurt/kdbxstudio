"""Qt local server compatible with KeePassXC-Browser / keepassxc-proxy."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from kdbxstudio.browser.protocol import BrowserProtocol, ProtocolContext
from kdbxstudio.core.paths import default_data_dir, ensure_private_dir

NATIVEMSG_MAX_LENGTH = 1024 * 1024


def keepassxc_browser_socket_path() -> str:
    """Same layout KeePassXC uses on Linux."""
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime:
        runtime = str(Path.home() / ".cache")
    sub = Path(runtime) / "app" / "org.keepassxc.KeePassXC"
    ensure_private_dir(sub)
    socket_path = sub / "org.keepassxc.KeePassXC.BrowserServer"
    # Legacy symlink for older proxies
    legacy = Path(runtime) / "org.keepassxc.KeePassXC.BrowserServer"
    try:
        if legacy.is_symlink() or legacy.exists():
            legacy.unlink()
        legacy.symlink_to(socket_path)
    except OSError:
        pass
    return str(socket_path)


def kdbxstudio_browser_socket_path() -> str:
    root = ensure_private_dir(default_data_dir())
    return str(root / "browser.sock")


class BrowserLocalServer(QObject):
    """Accept keepassxc-proxy (or our host) connections and run the protocol."""

    associate_requested = Signal(str)  # database label
    status_message = Signal(str)

    def __init__(
        self,
        context_factory: Callable[[], ProtocolContext],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._context_factory = context_factory
        self._protocol: BrowserProtocol | None = None
        self._servers: list[QLocalServer] = []
        self._associate_result: str | None = None
        self._associate_loop: QEventLoop | None = None
        self._buffers: dict[QLocalSocket, bytearray] = {}

    @property
    def running(self) -> bool:
        return any(s.isListening() for s in self._servers)

    def start(self) -> list[str]:
        self.stop()
        self._protocol = BrowserProtocol(self._context_factory())
        paths = [keepassxc_browser_socket_path(), kdbxstudio_browser_socket_path()]
        started: list[str] = []
        for path in paths:
            server = QLocalServer(self)
            server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
            QLocalServer.removeServer(path)
            if not server.listen(path):
                continue
            server.newConnection.connect(self._on_connection)
            self._servers.append(server)
            started.append(path)
        return started

    def stop(self) -> None:
        for server in self._servers:
            path = server.fullServerName()
            server.close()
            if path:
                QLocalServer.removeServer(path)
        self._servers.clear()
        self._buffers.clear()
        self._protocol = None

    def refresh_context(self) -> None:
        if self._protocol is not None:
            self._protocol.context = self._context_factory()

    def provide_associate_id(self, assoc_id: str | None) -> None:
        self._associate_result = assoc_id
        if self._associate_loop is not None:
            self._associate_loop.quit()

    def prompt_associate_blocking(self, db_label: str) -> str | None:
        """Ask the UI for an association name (must be called on GUI thread)."""
        self._associate_result = None
        self.associate_requested.emit(db_label)
        loop = QEventLoop()
        self._associate_loop = loop
        loop.exec()
        self._associate_loop = None
        return self._associate_result

    def _on_connection(self) -> None:
        for server in self._servers:
            while server.hasPendingConnections():
                socket = server.nextPendingConnection()
                if socket is None:
                    continue
                self._buffers[socket] = bytearray()
                socket.setReadBufferSize(NATIVEMSG_MAX_LENGTH)
                socket.readyRead.connect(lambda s=socket: self._on_ready(s))
                socket.disconnected.connect(lambda s=socket: self._buffers.pop(s, None))
                socket.disconnected.connect(socket.deleteLater)

    def _on_ready(self, socket: QLocalSocket) -> None:
        raw = bytes(socket.readAll().data())
        if not raw:
            return
        buffer = self._buffers.setdefault(socket, bytearray())
        buffer.extend(raw)
        if len(buffer) > NATIVEMSG_MAX_LENGTH:
            socket.write(b'{"action":"","errorCode":"13","error":"Message too large"}')
            socket.flush()
            socket.disconnectFromServer()
            return
        try:
            request = json.loads(bytes(buffer).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Local sockets may split one JSON object across several readyRead
            # signals.  Keep buffering until it is complete or reaches the cap.
            return
        buffer.clear()
        if self._protocol is None:
            self._protocol = BrowserProtocol(self._context_factory())
        # Ensure context is fresh (unlocked DB may have changed).
        self._protocol.context = self._context_factory()
        response = self._protocol.handle(request if isinstance(request, dict) else {})
        payload = json.dumps(response, separators=(",", ":")).encode("utf-8")
        socket.write(payload)
        socket.flush()
