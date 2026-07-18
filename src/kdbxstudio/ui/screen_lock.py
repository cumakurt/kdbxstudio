"""Optional screen-lock / session-lock hooks (Linux D-Bus)."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Slot
from PySide6.QtDBus import QDBusConnection


class ScreenLockWatcher(QObject):
    """Call ``on_lock`` when a known screensaver reports ActiveChanged(true).

    Best-effort: silently no-ops when D-Bus interfaces are unavailable.
    """

    def __init__(
        self,
        on_lock: Callable[[], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_lock = on_lock
        try:
            bus = QDBusConnection.sessionBus()
        except Exception:
            return
        if not bus.isConnected():
            return
        for service, path, interface in (
            (
                "org.freedesktop.ScreenSaver",
                "/org/freedesktop/ScreenSaver",
                "org.freedesktop.ScreenSaver",
            ),
            (
                "org.gnome.ScreenSaver",
                "/org/gnome/ScreenSaver",
                "org.gnome.ScreenSaver",
            ),
            (
                "org.mate.ScreenSaver",
                "/org/mate/ScreenSaver",
                "org.mate.ScreenSaver",
            ),
        ):
            try:
                bus.connect(
                    service,
                    path,
                    interface,
                    "ActiveChanged",
                    self,
                    "_on_active_changed",
                )
            except Exception:
                continue

    @Slot(bool)
    def _on_active_changed(self, active: bool) -> None:
        if active:
            self._on_lock()
