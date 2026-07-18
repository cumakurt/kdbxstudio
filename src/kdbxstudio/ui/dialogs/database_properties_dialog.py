"""Database properties dialog."""

from __future__ import annotations

from PySide6.QtWidgets import QDialogButtonBox, QFormLayout, QLabel, QWidget

from kdbxstudio.core.database import DatabaseInfo
from kdbxstudio.i18n import tr
from kdbxstudio.ui.widgets.dialog_shell import DialogShell


class DatabasePropertiesDialog(DialogShell):
    def __init__(self, info: DatabaseInfo, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            title=tr("Database Properties"),
            subtitle=tr("Encryption and vault statistics"),
            icon_name="info",
            width=480,
        )
        form = QFormLayout()
        form.addRow(tr("Path"), QLabel(info.path or tr("(unsaved)")))
        form.addRow(tr("KDBX version"), QLabel(info.version))
        form.addRow(tr("KDF"), QLabel(info.kdf_algorithm))
        form.addRow(tr("Encryption"), QLabel(info.encryption))
        form.addRow(tr("Entries"), QLabel(str(info.entry_count)))
        form.addRow(tr("Groups"), QLabel(str(info.group_count)))
        form.addRow(tr("Recycle Bin entries"), QLabel(str(info.recycle_bin_entries)))
        form.addRow(
            tr("Unsaved changes"),
            QLabel(tr("Yes") if info.dirty else tr("No")),
        )
        form.addRow(
            "",
            QLabel(
                tr(
                    "KDF parameters are set when the database is created. "
                    "Use a strong master password and optional key file."
                )
            ),
        )
        self.body.addLayout(form)
        # Close-only
        self.button_box.clear()
        close = self.button_box.addButton(QDialogButtonBox.StandardButton.Close)
        if close is not None:
            close.setProperty("cssClass", "primary")
            close.setDefault(True)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)
