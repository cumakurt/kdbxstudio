"""Dialog to create a new entry with all common fields."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QButtonGroup,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QWidget,
)

from kdbxstudio.i18n import tr
from kdbxstudio.security.session import ClipboardGuard
from kdbxstudio.ui.dialogs.password_generator_dialog import PasswordGeneratorDialog
from kdbxstudio.ui.theme.manager import polish_calendar_popup
from kdbxstudio.ui.theme.motion import fade_in
from kdbxstudio.ui.widgets.dialog_shell import DialogShell


@dataclass(frozen=True)
class NewEntryData:
    title: str
    username: str
    password: str
    url: str
    notes: str
    tags: tuple[str, ...]
    otp: str
    expires: bool
    expiry_date: str  # yyyy-MM-dd when expires is True


class NewEntryDialog(DialogShell):
    """Collect all common entry fields and create in one step."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        clipboard_guard: ClipboardGuard | None = None,
        group_path: str = "",
    ) -> None:
        super().__init__(
            parent,
            title=tr("New Entry"),
            subtitle=tr("Create a credential in the selected group"),
            icon_name="add",
            width=520,
        )
        self._clipboard_guard = clipboard_guard
        self._anim = None
        self.resize(520, 560)

        self._title = QLineEdit()
        self._title.setPlaceholderText(tr("Required"))
        self._username = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._url = QLineEdit()
        self._url.setPlaceholderText("https://")
        self._tags = QLineEdit()
        self._tags.setPlaceholderText(tr("Comma-separated tags"))
        self._otp = QLineEdit()
        self._otp.setPlaceholderText(tr("otpauth://… or base32 secret"))
        self._notes = QTextEdit()
        self._notes.setPlaceholderText(tr("Notes"))
        self._notes.setMinimumHeight(100)

        self._never_expires = QRadioButton(tr("Never expires"))
        self._has_expiry = QRadioButton(tr("Expires on"))
        self._never_expires.setChecked(True)
        expiry_mode = QButtonGroup(self)
        expiry_mode.addButton(self._never_expires)
        expiry_mode.addButton(self._has_expiry)

        self._expiry_date = QDateEdit()
        self._expiry_date.setCalendarPopup(True)
        self._expiry_date.setDisplayFormat("yyyy-MM-dd")
        self._expiry_date.setDate(QDate.currentDate().addYears(1))
        self._expiry_date.setMinimumDate(QDate(1970, 1, 1))
        self._expiry_date.setReadOnly(False)
        line = self._expiry_date.lineEdit()
        if line is not None:
            line.setReadOnly(False)
        self._expiry_date.setEnabled(False)
        polish_calendar_popup(self._expiry_date)
        self._has_expiry.toggled.connect(self._on_expiry_mode_toggled)
        self._expiry_date.dateChanged.connect(self._on_expiry_date_changed)

        show_btn = QPushButton(tr("Show"))
        show_btn.setCheckable(True)
        show_btn.toggled.connect(self._toggle_password)
        gen_btn = QPushButton(tr("Generate"))
        gen_btn.clicked.connect(self._generate_password)

        pwd_row = QHBoxLayout()
        pwd_row.addWidget(self._password, stretch=1)
        pwd_row.addWidget(show_btn)
        pwd_row.addWidget(gen_btn)

        expiry_mode_row = QHBoxLayout()
        expiry_mode_row.addWidget(self._never_expires)
        expiry_mode_row.addWidget(self._has_expiry)
        expiry_mode_row.addStretch(1)

        form = QFormLayout()
        if group_path:
            group_field = QLineEdit(group_path)
            group_field.setReadOnly(True)
            form.addRow(tr("Group"), group_field)
        form.addRow(tr("Title"), self._title)
        form.addRow(tr("Username"), self._username)
        form.addRow(tr("Password"), pwd_row)
        form.addRow(tr("URL"), self._url)
        form.addRow(tr("Tags"), self._tags)
        form.addRow(tr("TOTP"), self._otp)
        form.addRow(tr("Expiry"), expiry_mode_row)
        form.addRow(tr("Expiry date"), self._expiry_date)
        form.addRow(tr("Notes"), self._notes)
        self.body.addLayout(form)

        self.set_primary_text(tr("Create"))
        self.button_box.accepted.disconnect()
        self.button_box.accepted.connect(self._accept)
        self._title.setFocus()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        polish_calendar_popup(self._expiry_date)
        self._anim = fade_in(self)

    def entry_data(self) -> NewEntryData:
        tags = tuple(
            part.strip()
            for part in self._tags.text().split(",")
            if part.strip()
        )
        return NewEntryData(
            title=self._title.text().strip(),
            username=self._username.text().strip(),
            password=self._password.text(),
            url=self._url.text().strip(),
            notes=self._notes.toPlainText(),
            tags=tags,
            otp=self._otp.text().strip(),
            expires=self._has_expiry.isChecked(),
            expiry_date=self._expiry_date.date().toString("yyyy-MM-dd"),
        )

    def _on_expiry_mode_toggled(self, has_expiry: bool) -> None:
        self._expiry_date.setEnabled(has_expiry)
        self._expiry_date.setReadOnly(not has_expiry)
        line = self._expiry_date.lineEdit()
        if line is not None:
            line.setReadOnly(not has_expiry)
        if has_expiry:
            self._expiry_date.setFocus()

    def _on_expiry_date_changed(self, _date: QDate) -> None:
        if not self._has_expiry.isChecked():
            self._has_expiry.blockSignals(True)
            self._has_expiry.setChecked(True)
            self._has_expiry.blockSignals(False)
            self._expiry_date.setEnabled(True)
            self._expiry_date.setReadOnly(False)

    def _toggle_password(self, checked: bool) -> None:
        mode = (
            QLineEdit.EchoMode.Normal
            if checked
            else QLineEdit.EchoMode.Password
        )
        self._password.setEchoMode(mode)

    def _generate_password(self) -> None:
        dialog = PasswordGeneratorDialog(
            self, clipboard_guard=self._clipboard_guard
        )
        if dialog.exec() == PasswordGeneratorDialog.DialogCode.Accepted:
            self._password.setText(dialog.password())

    def _accept(self) -> None:
        if not self._title.text().strip():
            QMessageBox.warning(self, tr("New Entry"), tr("Title is required."))
            self._title.setFocus()
            return
        self.accept()
