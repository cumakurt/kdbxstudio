"""Change master password / key file dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from kdbxstudio.i18n import tr
from kdbxstudio.ui.theme.motion import fade_in
from kdbxstudio.ui.widgets.dialog_shell import DialogShell


class ChangeCredentialsDialog(DialogShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            title=tr("Change Master Password"),
            subtitle=tr("Update the database master password and key file"),
            icon_name="key",
            width=460,
        )
        self._anim = None
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._keyfile = QLineEdit()
        self._clear_key = QCheckBox(tr("Remove key file"))
        self._show = QCheckBox(tr("Show password"))
        self._show.toggled.connect(self._toggle)

        browse = QPushButton("…")
        browse.clicked.connect(self._browse)
        key_row = QHBoxLayout()
        key_row.addWidget(self._keyfile)
        key_row.addWidget(browse)

        form = QFormLayout()
        form.addRow(tr("New password"), self._password)
        form.addRow(tr("Confirm"), self._confirm)
        form.addRow(tr("Key file"), key_row)
        form.addRow("", self._clear_key)
        form.addRow("", self._show)
        self.body.addLayout(form)

        self.set_primary_text(tr("Change"))
        self.button_box.accepted.disconnect()
        self.button_box.accepted.connect(self._accept)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._anim = fade_in(self)

    def password(self) -> str | None:
        text = self._password.text()
        return text if text else None

    def clear_secrets(self) -> None:
        self._password.clear()
        self._confirm.clear()

    def keyfile(self) -> Path | None:
        text = self._keyfile.text().strip()
        return Path(text) if text else None

    def clear_keyfile(self) -> bool:
        return self._clear_key.isChecked()

    def _toggle(self, checked: bool) -> None:
        mode = (
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        self._password.setEchoMode(mode)
        self._confirm.setEchoMode(mode)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Select Key File"), str(Path.home()), tr("All Files (*)")
        )
        if path:
            self._keyfile.setText(path)
            self._clear_key.setChecked(False)

    def _accept(self) -> None:
        if self._password.text() != self._confirm.text():
            QMessageBox.warning(
                self, tr("Password mismatch"), tr("Passwords do not match.")
            )
            return
        if not self._password.text() and not self._keyfile.text().strip() and not self._clear_key.isChecked():
            QMessageBox.warning(
                self,
                tr("Missing credentials"),
                tr("Provide a password and/or a key file."),
            )
            return
        self.accept()
