"""Non-modal Security Dashboard window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget

from kdbxstudio.i18n import tr
from kdbxstudio.ui.security_dashboard.view import SecurityDashboardView
from kdbxstudio.ui.security_dashboard.view_model import SecurityDashboardViewModel


class SecurityDashboardDialog(QDialog):
    """Standalone resizable Security Dashboard."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("Security Dashboard"))
        self.setObjectName("securityDashboardDialog")
        self.setModal(False)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.resize(1280, 800)
        self.setMinimumSize(960, 640)
        self.view_model = SecurityDashboardViewModel(self)
        self.dashboard = SecurityDashboardView(self.view_model, self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.dashboard)


# Backwards-compatible alias for Password Health entry points
PasswordHealthDialog = SecurityDashboardDialog
