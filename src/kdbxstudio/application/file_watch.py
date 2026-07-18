"""Watch open KDBX files for external changes (Syncthing / Nextcloud / etc.)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, Signal


class DatabaseFileWatcher(QObject):
    """Debounced file-change notifications for open vault paths."""

    path_changed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._pending: dict[str, QTimer] = {}
        self._ignored: set[str] = set()

    def set_paths(self, paths: list[Path | str]) -> None:
        current = set(self._watcher.files())
        wanted = {str(Path(p).resolve()) for p in paths if p}
        for path in current - wanted:
            self._watcher.removePath(path)
        for path in wanted - current:
            if Path(path).is_file():
                self._watcher.addPath(path)

    def ignore_briefly(self, path: Path | str, *, ms: int = 1500) -> None:
        """Ignore self-saves so we do not prompt after our own write."""
        key = str(Path(path).resolve())
        self._ignored.add(key)

        def _clear() -> None:
            self._ignored.discard(key)

        QTimer.singleShot(ms, _clear)

    def _on_file_changed(self, path: str) -> None:
        key = str(Path(path).resolve())
        if key in self._ignored:
            # Re-add watch; some editors replace the inode.
            if Path(key).is_file() and key not in self._watcher.files():
                self._watcher.addPath(key)
            return
        timer = self._pending.get(key)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(400)
            timer.timeout.connect(lambda p=key: self._emit(p))
            self._pending[key] = timer
        timer.start()
        # QFileSystemWatcher often drops the path after a replace.
        if Path(key).is_file() and key not in self._watcher.files():
            self._watcher.addPath(key)

    def _emit(self, path: str) -> None:
        self._pending.pop(path, None)
        if path in self._ignored:
            return
        self.path_changed.emit(path)
