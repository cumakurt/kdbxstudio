"""Database properties dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.core.database import DatabaseInfo


class DatabasePropertiesDialog(QDialog):
    def __init__(self, info: DatabaseInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Database Properties")
        self.setModal(True)

        form = QFormLayout()
        form.addRow("Path", QLabel(info.path or "(unsaved)"))
        form.addRow("KDBX version", QLabel(info.version))
        form.addRow("KDF", QLabel(info.kdf_algorithm))
        form.addRow("Encryption", QLabel(info.encryption))
        form.addRow("Entries", QLabel(str(info.entry_count)))
        form.addRow("Groups", QLabel(str(info.group_count)))
        form.addRow("Recycle Bin entries", QLabel(str(info.recycle_bin_entries)))
        form.addRow("Unsaved changes", QLabel("Yes" if info.dirty else "No"))
        form.addRow(
            "",
            QLabel(
                "KDF parameters are set when the database is created. "
                "Use a strong master password and optional key file."
            ),
        )

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
