"""Password Health dialog — full-size findings browser."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from kdbxstudio.i18n import tr
from kdbxstudio.ui.widgets.audit_dashboard import AuditDashboardWidget


class PasswordHealthDialog(QDialog):
    """Standalone window for password health summary and findings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("Password Health"))
        self.setModal(False)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.resize(880, 600)
        self.setMinimumSize(640, 420)

        self.dashboard = AuditDashboardWidget(self)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        buttons.accepted.connect(self.close)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.dashboard, stretch=1)
        layout.addWidget(buttons)
