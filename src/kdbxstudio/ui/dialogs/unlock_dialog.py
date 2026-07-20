"""Open / create database credential dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPropertyAnimation
from PySide6.QtGui import QAction, QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from kdbxstudio.i18n import tr
from kdbxstudio.ui.icons import ICON_KEY, ICON_LOCK, ICON_OPEN, standard_icon
from kdbxstudio.ui.theme import current_ui_scale
from kdbxstudio.ui.theme.motion import fade_in
from kdbxstudio.ui.widgets.dialog_shell import DialogShell


def _lead(edit: QLineEdit, icon_name: str) -> None:
    action = QAction(edit)
    action.setIcon(standard_icon(icon_name))
    edit.addAction(action, QLineEdit.ActionPosition.LeadingPosition)


class UnlockDialog(DialogShell):
    """Collect password and optional key file for open/create."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        path: Path | None = None,
        create_mode: bool = False,
    ) -> None:
        title = tr("Create Database") if create_mode else tr("Unlock Database")
        subtitle = (
            tr("Choose a path and set master credentials")
            if create_mode
            else tr("Enter master password and optional key file")
        )
        super().__init__(
            parent,
            title=title,
            subtitle=subtitle,
            icon_name="add" if create_mode else ICON_LOCK,
            width=520,
        )
        self._path = path
        self._create_mode = create_mode
        self._anim: QPropertyAnimation | None = None
        scale = current_ui_scale()
        self.setMinimumWidth(scale.px(460))

        self._path_edit = QLineEdit(str(path) if path else "")
        self._path_edit.setReadOnly(not create_mode and path is not None)
        _lead(self._path_edit, ICON_OPEN)
        browse = QPushButton(tr("Browse…"))
        browse.setAutoDefault(False)
        browse.setDefault(False)
        browse.clicked.connect(self._browse_path)

        path_row = QHBoxLayout()
        path_row.addWidget(self._path_edit)
        path_row.addWidget(browse)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText(tr("Master password"))
        _lead(self._password, ICON_LOCK)

        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm.setPlaceholderText(tr("Confirm password"))
        self._confirm.setVisible(create_mode)
        _lead(self._confirm, ICON_LOCK)

        self._keyfile = QLineEdit()
        self._keyfile.setPlaceholderText(tr("Optional key file"))
        _lead(self._keyfile, ICON_KEY)
        key_browse = QPushButton(tr("…"))
        key_browse.setAutoDefault(False)
        key_browse.setDefault(False)
        key_browse.clicked.connect(self._browse_keyfile)
        key_row = QHBoxLayout()
        key_row.addWidget(self._keyfile)
        key_row.addWidget(key_browse)

        self._show_password = QCheckBox(tr("Show password"))
        self._show_password.toggled.connect(self._toggle_password)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow(tr("Database"), path_row)
        form.addRow(tr("Password"), self._password)
        if create_mode:
            form.addRow(tr("Confirm"), self._confirm)
        form.addRow(tr("Key file"), key_row)
        form.addRow("", self._show_password)
        self.body.addLayout(form)

        self.set_primary_text(tr("Create") if create_mode else tr("Unlock"))
        ok = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok is not None:
            ok.setMinimumWidth(scale.px(120))
            ok.setAutoDefault(True)
            ok.setDefault(True)
        self.button_box.accepted.disconnect()
        self.button_box.accepted.connect(self._accept)
        self._password.returnPressed.connect(self._accept)
        self._confirm.returnPressed.connect(self._accept)
        self._password.setFocus()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self._anim = fade_in(self)

    def database_path(self) -> Path:
        return Path(self._path_edit.text().strip())

    def password(self) -> str | None:
        text = self._password.text()
        return text if text else None

    def clear_secrets(self) -> None:
        """Wipe credential widgets after the caller has consumed the values."""
        self._password.clear()
        self._confirm.clear()

    def keyfile(self) -> Path | None:
        text = self._keyfile.text().strip()
        return Path(text) if text else None

    def _toggle_password(self, checked: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self._password.setEchoMode(mode)
        self._confirm.setEchoMode(mode)

    def _browse_path(self) -> None:
        if self._create_mode:
            path, _ = QFileDialog.getSaveFileName(
                self,
                tr("Create KDBX Database"),
                str(Path.home()),
                tr("KeePass Database (*.kdbx)"),
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                tr("Open KDBX Database"),
                str(Path.home()),
                tr("KeePass Database (*.kdbx)"),
            )
        if path:
            self._path_edit.setText(path)

    def _browse_keyfile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Select Key File"),
            str(Path.home()),
            tr("All Files (*)"),
        )
        if path:
            self._keyfile.setText(path)

    def _accept(self) -> None:
        if not self._path_edit.text().strip():
            QMessageBox.warning(self, tr("Missing path"), tr("Choose a database path."))
            return
        if self._create_mode:
            if not self._password.text() and not self._keyfile.text().strip():
                QMessageBox.warning(
                    self,
                    tr("Missing credentials"),
                    tr("Provide a password and/or a key file."),
                )
                return
            if self._password.text() != self._confirm.text():
                QMessageBox.warning(
                    self, tr("Password mismatch"), tr("Passwords do not match.")
                )
                return
        self.accept()
