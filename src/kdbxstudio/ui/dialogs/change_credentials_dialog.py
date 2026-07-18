"""Change master password / key file dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ChangeCredentialsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Change Master Password")
        self.setModal(True)
        self.resize(420, 220)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._keyfile = QLineEdit()
        self._clear_key = QCheckBox("Remove key file")
        self._show = QCheckBox("Show password")
        self._show.toggled.connect(self._toggle)

        browse = QPushButton("…")
        browse.clicked.connect(self._browse)
        key_row = QHBoxLayout()
        key_row.addWidget(self._keyfile)
        key_row.addWidget(browse)

        form = QFormLayout()
        form.addRow("New password", self._password)
        form.addRow("Confirm", self._confirm)
        form.addRow("Key file", key_row)
        form.addRow("", self._clear_key)
        form.addRow("", self._show)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn is not None:
            ok_btn.setProperty("cssClass", "primary")
            ok_btn.setDefault(True)
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn is not None:
            cancel_btn.setProperty("cssClass", "secondary")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def password(self) -> str | None:
        text = self._password.text()
        return text if text else None

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
            self, "Select Key File", str(Path.home()), "All Files (*)"
        )
        if path:
            self._keyfile.setText(path)
            self._clear_key.setChecked(False)

    def _accept(self) -> None:
        if self._password.text() != self._confirm.text():
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return
        if (
            not self._password.text()
            and not self._keyfile.text().strip()
            and not self._clear_key.isChecked()
        ):
            QMessageBox.warning(
                self,
                "No changes",
                "Provide a new password and/or key file, or clear the key file.",
            )
            return
        self.accept()
