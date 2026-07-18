"""Scrollable Security Dashboard view bound to a ViewModel."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.application.security_dashboard.models import DashboardSnapshot
from kdbxstudio.i18n import tr
from kdbxstudio.ui.security_dashboard.panel_base import DashboardPanel
from kdbxstudio.ui.security_dashboard.panel_registry import registered_panels
from kdbxstudio.ui.security_dashboard.panels import register_default_panels
from kdbxstudio.ui.security_dashboard.view_model import SecurityDashboardViewModel


class SecurityDashboardView(QWidget):
    def __init__(
        self,
        view_model: SecurityDashboardViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("securityDashboard")
        self._vm = view_model
        register_default_panels()

        self._empty = QLabel(tr("No database open"))
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setObjectName("securityDashboardEmpty")

        refresh = QPushButton(tr("Refresh"))
        refresh.setAccessibleName(tr("Refresh security dashboard"))
        refresh.clicked.connect(self._vm.request_refresh)

        top = QHBoxLayout()
        top.addWidget(QLabel(tr("Security Dashboard")), stretch=1)
        top.addWidget(refresh)

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(12)
        self._panels: list[DashboardPanel] = []

        columns = 2
        row = col = 0
        for spec in registered_panels():
            panel = spec.factory()
            panel.entry_activated.connect(self._vm.activate_entry)
            panel.fix_next_requested.connect(self._vm.request_fix_next)
            span = min(spec.span, columns)
            if col + span > columns:
                row += 1
                col = 0
            self._grid.addWidget(panel, row, col, 1, span)
            col += span
            if col >= columns:
                row += 1
                col = 0
            self._panels.append(panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self._grid_host)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addLayout(top)
        layout.addWidget(self._empty)
        layout.addWidget(scroll, stretch=1)
        self._scroll = scroll

        self._vm.snapshot_changed.connect(self._on_snapshot)
        self._on_snapshot(self._vm.snapshot)

    def _on_snapshot(self, snapshot: object) -> None:
        if not isinstance(snapshot, DashboardSnapshot):
            self._empty.setVisible(True)
            self._scroll.setVisible(False)
            return
        self._empty.setVisible(False)
        self._scroll.setVisible(True)
        for panel in self._panels:
            panel.update_snapshot(snapshot)
