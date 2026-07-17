"""Open / create database credential dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.ui.icons import ICON_KEY, ICON_LOCK, ICON_OPEN, standard_icon
from kdbxstudio.ui.theme import current_ui_scale


def _lead(edit: QLineEdit, icon_name: str) -> None:
    action = QAction(edit)
    action.setIcon(standard_icon(icon_name))
    edit.addAction(action, QLineEdit.ActionPosition.LeadingPosition)


class UnlockDialog(QDialog):
    """Collect password and optional key file for open/create."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        path: Path | None = None,
        create_mode: bool = False,
    ) -> None:
        super().__init__(parent)
        self._path = path
        self._create_mode = create_mode
        self.setWindowTitle("Create Database" if create_mode else "Unlock Database")
        self.setModal(True)
        scale = current_ui_scale()
        self.setMinimumWidth(scale.px(460))

        self._path_edit = QLineEdit(str(path) if path else "")
        self._path_edit.setReadOnly(not create_mode and path is not None)
        _lead(self._path_edit, ICON_OPEN)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_path)

        path_row = QHBoxLayout()
        path_row.addWidget(self._path_edit)
        path_row.addWidget(browse)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("Master password")
        _lead(self._password, ICON_LOCK)

        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm.setPlaceholderText("Confirm password")
        self._confirm.setVisible(create_mode)
        _lead(self._confirm, ICON_LOCK)

        self._keyfile = QLineEdit()
        self._keyfile.setPlaceholderText("Optional key file")
        _lead(self._keyfile, ICON_KEY)
        key_browse = QPushButton("…")
        key_browse.clicked.connect(self._browse_keyfile)
        key_row = QHBoxLayout()
        key_row.addWidget(self._keyfile)
        key_row.addWidget(key_browse)

        self._show_password = QCheckBox("Show password")
        self._show_password.toggled.connect(self._toggle_password)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("Database", path_row)
        form.addRow("Password", self._password)
        if create_mode:
            form.addRow("Confirm", self._confirm)
        form.addRow("Key file", key_row)
        form.addRow("", self._show_password)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn is not None:
            ok_btn.setText("Create" if create_mode else "Unlock")
            ok_btn.setProperty("cssClass", "primary")
            ok_btn.setDefault(True)
            ok_btn.setMinimumWidth(scale.px(120))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        card = QWidget()
        card.setObjectName("unlockCard")
        card.setFixedWidth(scale.px(420))
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(
            scale.px(24), scale.px(24), scale.px(24), scale.px(24)
        )
        card_layout.setSpacing(scale.px(16))
        heading = QLabel(self.windowTitle())
        heading.setObjectName("emptyBrand")
        card_layout.addWidget(heading)
        card_layout.addLayout(form)
        card_layout.addWidget(buttons)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.addStretch()
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch()

        self._password.setFocus()

    def database_path(self) -> Path:
        return Path(self._path_edit.text().strip())

    def password(self) -> str | None:
        text = self._password.text()
        return text if text else None

    def keyfile(self) -> Path | None:
        text = self._keyfile.text().strip()
        return Path(text) if text else None

    def _toggle_password(self, checked: bool) -> None:
        mode = (
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        self._password.setEchoMode(mode)
        self._confirm.setEchoMode(mode)

    def _browse_path(self) -> None:
        if self._create_mode:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Create KDBX Database",
                str(Path.home()),
                "KeePass Database (*.kdbx)",
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Open KDBX Database",
                str(Path.home()),
                "KeePass Database (*.kdbx)",
            )
        if path:
            self._path_edit.setText(path)

    def _browse_keyfile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Key File",
            str(Path.home()),
            "All Files (*)",
        )
        if path:
            self._keyfile.setText(path)

    def _accept(self) -> None:
        if not self._path_edit.text().strip():
            QMessageBox.warning(self, "Missing path", "Choose a database path.")
            return
        if self._create_mode:
            if not self._password.text() and not self._keyfile.text().strip():
                QMessageBox.warning(
                    self,
                    "Missing credentials",
                    "Provide a password and/or a key file.",
                )
                return
            if self._password.text() != self._confirm.text():
                QMessageBox.warning(
                    self, "Password mismatch", "Passwords do not match."
                )
                return
        self.accept()
