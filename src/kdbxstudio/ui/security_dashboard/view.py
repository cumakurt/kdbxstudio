"""Scrollable Security Dashboard view bound to a ViewModel."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
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
        self._hidden_panels: set[str] = set()
        self._panel_by_id: dict[str, object] = {}
        register_default_panels()

        self._empty = QLabel(tr("No database open"))
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setObjectName("securityDashboardEmpty")

        refresh = QPushButton(tr("Refresh"))
        refresh.setAccessibleName(tr("Refresh security dashboard"))
        refresh.clicked.connect(self._vm.request_refresh)
        layout_btn = QPushButton(tr("Panels"))
        layout_btn.setProperty("cssClass", "secondary")
        layout_btn.clicked.connect(self._show_panel_menu)

        top = QHBoxLayout()
        top.addWidget(QLabel(tr("Security Dashboard")), stretch=1)
        top.addWidget(layout_btn)
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
            self._panel_by_id[spec.id] = panel

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


    def set_hidden_panels(self, panel_ids: set[str] | list[str] | str) -> None:
        if isinstance(panel_ids, str):
            hidden = {p.strip() for p in panel_ids.split(",") if p.strip()}
        else:
            hidden = set(panel_ids)
        self._hidden_panels = hidden
        for panel_id, panel in self._panel_by_id.items():
            panel.setVisible(panel_id not in hidden)

    def hidden_panels_csv(self) -> str:
        return ",".join(sorted(self._hidden_panels))

    def _show_panel_menu(self) -> None:
        menu = QMenu(self)
        for spec in registered_panels():
            action = menu.addAction(tr(spec.title))
            action.setCheckable(True)
            action.setChecked(spec.id not in self._hidden_panels)

            def _toggle(checked: bool, panel_id: str = spec.id) -> None:
                if checked:
                    self._hidden_panels.discard(panel_id)
                else:
                    self._hidden_panels.add(panel_id)
                panel = self._panel_by_id.get(panel_id)
                if panel is not None:
                    panel.setVisible(panel_id not in self._hidden_panels)

            action.toggled.connect(_toggle)
        menu.exec(self.mapToGlobal(self.rect().topRight()))
