"""Clipboard timeout and session lock helpers."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer, Signal


class ClipboardGuard(QObject):
    """Copies text to the clipboard and clears it after a timeout."""

    cleared = Signal()

    def __init__(
        self,
        clipboard_setter: Callable[[str], None],
        clipboard_clear: Callable[[], None],
        timeout_ms: int = 15_000,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._set = clipboard_setter
        self._clear = clipboard_clear
        self._timeout_ms = timeout_ms
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

    def copy(self, text: str, timeout_ms: int | None = None) -> None:
        self._set(text)
        self._timer.stop()
        effective = timeout_ms if timeout_ms is not None else self._timeout_ms
        if effective > 0:
            self._timer.start(effective)

    def set_timeout(self, timeout_ms: int) -> None:
        self._timeout_ms = max(0, timeout_ms)

    def cancel(self) -> None:
        """Stop the clear timer and wipe the clipboard immediately."""
        self._timer.stop()
        self._clear()
        self.cleared.emit()

    def _on_timeout(self) -> None:
        self._clear()
        self.cleared.emit()


class AutoLockController(QObject):
    """Emits lock_requested after idle timeout (session lock hook)."""

    lock_requested = Signal()

    def __init__(
        self,
        idle_timeout_ms: int = 5 * 60_000,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.lock_requested.emit)
        self._idle_timeout_ms = idle_timeout_ms
        self._enabled = True

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self._timer.stop()

    def set_timeout(self, idle_timeout_ms: int) -> None:
        self._idle_timeout_ms = max(0, idle_timeout_ms)
        if self._enabled and self._idle_timeout_ms > 0:
            self.activity()
        else:
            self._timer.stop()

    def activity(self) -> None:
        if not self._enabled or self._idle_timeout_ms <= 0:
            return
        self._timer.stop()
        self._timer.start(self._idle_timeout_ms)

    def stop(self) -> None:
        self._timer.stop()
