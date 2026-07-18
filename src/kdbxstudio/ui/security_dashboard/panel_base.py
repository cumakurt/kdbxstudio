"""Base panel contract for Security Dashboard modules."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from kdbxstudio.application.security_dashboard.models import DashboardSnapshot
from kdbxstudio.i18n import tr


class DashboardPanel(QFrame):
    """Framed panel with title; subclasses implement ``update_snapshot``."""

    entry_activated = Signal(str)
    fix_next_requested = Signal(str, str)

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("securityDashboardPanel")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._title = QLabel(tr(title))
        self._title.setObjectName("securityPanelTitle")
        self._body = QVBoxLayout()
        self._body.setContentsMargins(0, 0, 0, 0)
        self._body.setSpacing(8)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)
        root.addWidget(self._title)
        root.addLayout(self._body, stretch=1)

    def update_snapshot(self, snapshot: DashboardSnapshot) -> None:
        raise NotImplementedError
