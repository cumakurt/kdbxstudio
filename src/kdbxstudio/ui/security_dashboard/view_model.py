"""Security Dashboard ViewModel (lightweight MVVM binder)."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from kdbxstudio.application.security_dashboard.models import DashboardSnapshot


class SecurityDashboardViewModel(QObject):
    """Holds the latest snapshot and forwards UI intents."""

    snapshot_changed = Signal(object)  # DashboardSnapshot | None
    refresh_requested = Signal()
    entry_activated = Signal(str)
    fix_next_requested = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._snapshot: DashboardSnapshot | None = None

    @property
    def snapshot(self) -> DashboardSnapshot | None:
        return self._snapshot

    def set_snapshot(self, snapshot: DashboardSnapshot | None) -> None:
        self._snapshot = snapshot
        self.snapshot_changed.emit(snapshot)

    def clear(self) -> None:
        self.set_snapshot(None)

    def request_refresh(self) -> None:
        self.refresh_requested.emit()

    def activate_entry(self, entry_uuid: str) -> None:
        self.entry_activated.emit(entry_uuid)

    def request_fix_next(self, kind: str, entry_uuid: str) -> None:
        self.fix_next_requested.emit(kind, entry_uuid)
