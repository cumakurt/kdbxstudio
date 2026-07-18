"""Entry detail editor with contextual field icons."""

from __future__ import annotations

from PySide6.QtCore import QDate, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDateEdit,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.application.expiry import (
    expiry_chip_info,
    expiry_local_date_iso,
    local_date_to_utc_end_of_day,
)
from kdbxstudio.core.database import EntryView
from kdbxstudio.core.password_strength import (
    StrengthBucket,
    estimate_password_strength,
    strength_tone,
)
from kdbxstudio.i18n import tr, trf
from kdbxstudio.security.session import ClipboardGuard
from kdbxstudio.ui.icons.entry_type import (
    EntryKind,
    FieldKind,
    detect_entry_kind,
    field_icon,
)
from kdbxstudio.ui.theme.manager import polish_calendar_popup, set_widget_tone
from kdbxstudio.ui.widgets.notes_preview import NotesPreviewWidget
from kdbxstudio.ui.widgets.status_chip import StatusChip
from kdbxstudio.ui.widgets.tag_colors import tag_chip_colors

_STRENGTH_LABELS = {
    StrengthBucket.EMPTY: "Empty",
    StrengthBucket.VERY_WEAK: "Very Weak",
    StrengthBucket.WEAK: "Weak",
    StrengthBucket.FAIR: "Fair",
    StrengthBucket.GOOD: "Good",
    StrengthBucket.STRONG: "Strong",
}


def _leading_icon(edit: QLineEdit, icon_kind: FieldKind) -> QAction:
    action = QAction(edit)
    action.setIcon(field_icon(icon_kind))
    edit.addAction(action, QLineEdit.ActionPosition.LeadingPosition)
    return action


def _estimate_password_strength(password: str) -> tuple[int, str]:
    score, bucket = estimate_password_strength(password)
    return score, tr(_STRENGTH_LABELS[bucket])


def _strength_tone(score: int) -> str:
    return strength_tone(score)


class EntryDetailWidget(QWidget):
    """View / edit a single entry."""

    save_requested = Signal(dict)
    copy_password_requested = Signal(str)
    generate_password_requested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        clipboard_guard: ClipboardGuard | None = None,
    ) -> None:
        super().__init__(parent)
        self._clipboard_guard = clipboard_guard
        self._entry_uuid: str | None = None
        self._entry_kind = EntryKind.GENERIC

        self._kind_badge = QLabel()
        self._kind_badge.setObjectName("entryKindBadge")
        self._kind_badge.setFixedSize(20, 20)

        self._title = QLineEdit()
        self._username = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._strength_bar = QProgressBar()
        self._strength_bar.setRange(0, 100)
        self._strength_bar.setValue(0)
        self._strength_bar.setTextVisible(True)
        self._strength_bar.setMaximumHeight(8)
        self._strength_bar.setFormat("")
        self._strength_label = QLabel("")
        set_widget_tone(self._strength_label, "secondary")
        self._url = QLineEdit()
        self._notes = NotesPreviewWidget()
        self._tags = QLineEdit()
        self._tags.setPlaceholderText(tr("Comma-separated tags"))
        self._never_expires = QRadioButton(tr("Never expires"))
        self._has_expiry = QRadioButton(tr("Expires on"))
        self._never_expires.setChecked(True)
        self._expiry_mode = QButtonGroup(self)
        self._expiry_mode.addButton(self._never_expires)
        self._expiry_mode.addButton(self._has_expiry)

        self._expiry_date = QDateEdit()
        self._expiry_date.setCalendarPopup(True)
        self._expiry_date.setDisplayFormat("yyyy-MM-dd")
        self._expiry_date.setDate(QDate.currentDate().addYears(1))
        self._expiry_date.setMinimumDate(QDate(1970, 1, 1))
        self._expiry_date.setReadOnly(False)
        line = self._expiry_date.lineEdit()
        if line is not None:
            line.setReadOnly(False)
            line.setPlaceholderText(tr("YYYY-MM-DD"))
        self._expiry_date.setEnabled(False)
        polish_calendar_popup(self._expiry_date)
        self._form_enabled = False
        self._has_expiry.toggled.connect(self._on_expiry_mode_toggled)
        self._expiry_date.dateChanged.connect(self._on_expiry_date_changed)

        self._expiry_countdown = StatusChip(object_name="expiryChip")
        self._tag_chips = QHBoxLayout()
        self._tag_chips.setSpacing(4)

        expiry_mode_row = QHBoxLayout()
        expiry_mode_row.addWidget(self._never_expires)
        expiry_mode_row.addWidget(self._has_expiry)
        expiry_mode_row.addStretch(1)

        self._title_icon = _leading_icon(self._title, FieldKind.TITLE)
        self._username_icon = _leading_icon(self._username, FieldKind.USERNAME)
        self._password_icon = _leading_icon(self._password, FieldKind.PASSWORD)
        self._url_icon = _leading_icon(self._url, FieldKind.URL)

        self._title.textChanged.connect(self._refresh_field_icons)
        self._url.textChanged.connect(self._refresh_field_icons)
        self._username.textChanged.connect(self._refresh_field_icons)
        self._password.textChanged.connect(self._update_strength)

        self._custom = QTableWidget(0, 2)
        self._custom.setHorizontalHeaderLabels([tr("Key"), tr("Value")])
        self._custom.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._custom.horizontalHeader().setHighlightSections(False)
        self._custom.verticalHeader().setVisible(False)
        self._custom.setShowGrid(False)
        self._custom.setFrameShape(QFrame.Shape.NoFrame)
        self._custom.setAlternatingRowColors(True)
        self._custom.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._custom.customContextMenuRequested.connect(self._show_custom_menu)

        copy_btn = QPushButton(tr("Copy"))
        copy_btn.setIcon(field_icon(FieldKind.COPY))
        copy_btn.setIconSize(QSize(14, 14))
        copy_btn.setToolTip(tr("Copy password"))
        copy_btn.clicked.connect(self._copy_password)

        self._show_btn = QPushButton(tr("Show"))
        self._show_btn.setIcon(field_icon(FieldKind.SHOW))
        self._show_btn.setIconSize(QSize(14, 14))
        self._show_btn.setCheckable(True)
        self._show_btn.toggled.connect(self._toggle_password)

        gen_btn = QPushButton(tr("Generate"))
        gen_btn.setIcon(field_icon(FieldKind.GENERATE))
        gen_btn.setIconSize(QSize(14, 14))
        gen_btn.clicked.connect(self.generate_password_requested.emit)

        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(4)
        pwd_row.addWidget(self._password, stretch=1)
        pwd_row.addWidget(self._show_btn)
        pwd_row.addWidget(copy_btn)
        pwd_row.addWidget(gen_btn)

        strength_row = QHBoxLayout()
        strength_row.setSpacing(8)
        strength_row.addWidget(self._strength_bar, stretch=1)
        strength_row.addWidget(self._strength_label)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(self._kind_badge)
        title_row.addWidget(self._title, stretch=1)

        add_prop = QPushButton(tr("Add field"))
        add_prop.setIcon(field_icon(FieldKind.CUSTOM))
        add_prop.setIconSize(QSize(14, 14))
        add_prop.clicked.connect(self._add_custom_row)
        del_prop = QPushButton(tr("Remove field"))
        del_prop.setProperty("cssClass", "ghost")
        del_prop.clicked.connect(self._remove_custom_row)
        prop_btns = QHBoxLayout()
        prop_btns.addWidget(add_prop)
        prop_btns.addWidget(del_prop)
        prop_btns.addStretch()

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow(tr("Title"), title_row)
        form.addRow(tr("Username"), self._username)
        form.addRow(tr("Password"), pwd_row)
        form.addRow(tr("Strength"), strength_row)
        form.addRow(tr("URL"), self._url)
        form.addRow(tr("Tags"), self._tags)
        form.addRow("", self._tag_chips)
        form.addRow(tr("Expiry"), expiry_mode_row)
        form.addRow(tr("Expiry date"), self._expiry_date)
        form.addRow("", self._expiry_countdown)
        form.addRow(tr("Notes"), self._notes)
        form.addRow(tr("Custom fields"), self._custom)
        form.addRow("", prop_btns)

        save_btn = QPushButton(tr("Save entry"))
        save_btn.setIcon(field_icon(FieldKind.SAVE))
        save_btn.setIconSize(QSize(14, 14))
        save_btn.clicked.connect(self._emit_save)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        layout.addLayout(form)
        layout.addWidget(save_btn)
        self.set_enabled(False)
        self._apply_kind_icons(EntryKind.GENERIC)

    def set_enabled(self, enabled: bool) -> None:
        self._form_enabled = enabled
        for widget in (
            self._title,
            self._username,
            self._password,
            self._url,
            self._tags,
            self._never_expires,
            self._has_expiry,
            self._notes,
            self._custom,
        ):
            widget.setEnabled(enabled)
        self._sync_expiry_date_enabled()

    def clear(self) -> None:
        self._entry_uuid = None
        self._title.blockSignals(True)
        self._url.blockSignals(True)
        self._username.blockSignals(True)
        self._title.clear()
        self._username.clear()
        self._password.clear()
        self._url.clear()
        self._tags.clear()
        self._clear_tag_chips()
        self._never_expires.setChecked(True)
        self._expiry_date.blockSignals(True)
        self._expiry_date.setDate(QDate.currentDate().addYears(1))
        self._expiry_date.blockSignals(False)
        self._expiry_countdown.clear_chip()
        self._title.blockSignals(False)
        self._url.blockSignals(False)
        self._username.blockSignals(False)
        self._notes.clear()
        self._custom.setRowCount(0)
        self._reset_password_visibility()
        self._apply_kind_icons(EntryKind.GENERIC)
        self.set_enabled(False)

    def load_entry(self, entry: EntryView) -> None:
        self._entry_uuid = entry.uuid
        self._title.blockSignals(True)
        self._url.blockSignals(True)
        self._username.blockSignals(True)
        self._expiry_date.blockSignals(True)
        self._title.setText(entry.title)
        self._username.setText(entry.username)
        self._password.setText(entry.password)
        self._url.setText(entry.url)
        self._tags.setText(", ".join(entry.tags))
        self._refresh_tag_chips(entry.tags)
        if entry.expires:
            self._has_expiry.setChecked(True)
        else:
            self._never_expires.setChecked(True)
        local_iso = expiry_local_date_iso(entry)
        if local_iso:
            date = QDate.fromString(local_iso, "yyyy-MM-dd")
            if date.isValid():
                self._expiry_date.setDate(date)
        elif not entry.expires:
            self._expiry_date.setDate(QDate.currentDate().addYears(1))
        self._title.blockSignals(False)
        self._url.blockSignals(False)
        self._username.blockSignals(False)
        self._expiry_date.blockSignals(False)
        self._notes.setPlainText(entry.notes)
        self._load_custom(entry.custom_properties)
        kind = detect_entry_kind(
            title=entry.title,
            url=entry.url,
            username=entry.username,
            notes=entry.notes,
            custom_properties=entry.custom_properties,
        )
        self._apply_kind_icons(kind)
        self._update_expiry_countdown(entry)
        self._reset_password_visibility()
        self.set_enabled(True)

    def _sync_expiry_date_enabled(self) -> None:
        editable = self._form_enabled and self._has_expiry.isChecked()
        self._expiry_date.setEnabled(editable)
        self._expiry_date.setReadOnly(not editable)
        line = self._expiry_date.lineEdit()
        if line is not None:
            line.setReadOnly(not editable)

    def _on_expiry_mode_toggled(self, has_expiry: bool) -> None:
        self._sync_expiry_date_enabled()
        if has_expiry and self._form_enabled:
            self._expiry_date.setFocus(Qt.FocusReason.OtherFocusReason)
            self._refresh_expiry_countdown_from_editor()

    def _on_expiry_date_changed(self, _date: QDate) -> None:
        if not self._form_enabled:
            return
        if not self._has_expiry.isChecked():
            self._has_expiry.blockSignals(True)
            self._has_expiry.setChecked(True)
            self._has_expiry.blockSignals(False)
            self._sync_expiry_date_enabled()
        self._refresh_expiry_countdown_from_editor()

    def _refresh_expiry_countdown_from_editor(self) -> None:
        if not self._has_expiry.isChecked():
            self._expiry_countdown.clear_chip()
            return
        iso = self._expiry_date.date().toString("yyyy-MM-dd")
        stub = EntryView(
            uuid=self._entry_uuid or "",
            title="",
            username="",
            password="",
            url="",
            notes="",
            group_path="",
            expires=True,
            expiry_time=local_date_to_utc_end_of_day(iso).isoformat(),
        )
        self._update_expiry_countdown(stub)

    def _update_expiry_countdown(self, entry: EntryView) -> None:
        info = expiry_chip_info(entry)
        if info is None:
            self._expiry_countdown.clear_chip()
            return
        label = info.label
        if info.tone == "danger":
            text = trf("Expired {label}", label=label)
        elif label == "Today":
            text = tr("Expires today")
        else:
            text = trf("Expires in {label}", label=label)
        self._expiry_countdown.set_chip(text, info.tone)

    def _clear_tag_chips(self) -> None:
        while self._tag_chips.count():
            item = self._tag_chips.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_tag_chips(self, tags: tuple[str, ...] | list[str]) -> None:
        self._clear_tag_chips()
        for tag in tags:
            chip = QLabel(tag)
            chip.setObjectName("tagChip")
            bg, fg = tag_chip_colors(tag)
            chip.setStyleSheet(
                f"QLabel#tagChip {{ background-color: {bg}; color: {fg}; "
                f"border-radius: 8px; padding: 2px 8px; }}"
            )
            self._tag_chips.addWidget(chip)
        self._tag_chips.addStretch(1)

    def _refresh_field_icons(self) -> None:
        kind = detect_entry_kind(
            title=self._title.text(),
            url=self._url.text(),
            username=self._username.text(),
            notes=self._notes.toPlainText(),
            custom_properties=self._custom_as_dict(),
        )
        self._apply_kind_icons(kind)

    def _apply_kind_icons(self, kind: EntryKind) -> None:
        self._entry_kind = kind
        self._kind_badge.setPixmap(
            field_icon(FieldKind.TITLE, entry_kind=kind).pixmap(18, 18)
        )
        self._kind_badge.setToolTip(f"Detected type: {kind.value}")
        self._title_icon.setIcon(field_icon(FieldKind.TITLE, entry_kind=kind))
        self._username_icon.setIcon(field_icon(FieldKind.USERNAME, entry_kind=kind))
        self._password_icon.setIcon(field_icon(FieldKind.PASSWORD, entry_kind=kind))
        self._url_icon.setIcon(field_icon(FieldKind.URL, entry_kind=kind))
        hints = {
            EntryKind.API: tr("API key / token"),
            EntryKind.SSH: tr("Passphrase (optional)"),
            EntryKind.BANK: tr("Card number"),
            EntryKind.WIFI: tr("Wi-Fi password"),
            EntryKind.CERTIFICATE: tr("Key passphrase"),
            EntryKind.DATABASE: tr("Database password"),
        }
        self._password.setPlaceholderText(hints.get(kind, tr("Password")))
        user_hints = {
            EntryKind.EMAIL: tr("Email address"),
            EntryKind.SSH: tr("SSH user / comment"),
            EntryKind.BANK: tr("Cardholder name"),
            EntryKind.API: tr("Client id (optional)"),
        }
        self._username.setPlaceholderText(user_hints.get(kind, tr("Username")))

    def _load_custom(self, props: dict[str, str]) -> None:
        self._custom.setRowCount(0)
        for key, value in sorted(props.items()):
            row = self._custom.rowCount()
            self._custom.insertRow(row)
            self._custom.setItem(row, 0, QTableWidgetItem(key))
            self._custom.setItem(row, 1, QTableWidgetItem(value))

    def _custom_as_dict(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for row in range(self._custom.rowCount()):
            key_item = self._custom.item(row, 0)
            val_item = self._custom.item(row, 1)
            key = key_item.text().strip() if key_item else ""
            if not key:
                continue
            result[key] = val_item.text() if val_item else ""
        return result

    def _add_custom_row(self) -> None:
        row = self._custom.rowCount()
        self._custom.insertRow(row)
        self._custom.setItem(row, 0, QTableWidgetItem(""))
        self._custom.setItem(row, 1, QTableWidgetItem(""))

    def _remove_custom_row(self) -> None:
        row = self._custom.currentRow()
        if row >= 0:
            self._custom.removeRow(row)

    def _show_custom_menu(self, pos: QPoint) -> None:
        item = self._custom.itemAt(pos)
        if item is not None:
            self._custom.setCurrentItem(item)
        row = self._custom.currentRow()
        has_row = row >= 0
        menu = QMenu(self)
        menu.addAction(tr("Add field"), self._add_custom_row)
        remove = menu.addAction(tr("Remove field"), self._remove_custom_row)
        remove.setEnabled(has_row)
        menu.addSeparator()
        copy_key = menu.addAction(tr("Copy key"), lambda: self._copy_custom_cell(0))
        copy_val = menu.addAction(tr("Copy value"), lambda: self._copy_custom_cell(1))
        copy_key.setEnabled(has_row)
        copy_val.setEnabled(has_row)
        menu.exec(self._custom.mapToGlobal(pos))

    def _copy_custom_cell(self, column: int) -> None:
        row = self._custom.currentRow()
        if row < 0:
            return
        cell = self._custom.item(row, column)
        text = cell.text() if cell else ""
        if self._clipboard_guard is not None:
            self._clipboard_guard.copy(text)
            return
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)

    def set_password(self, password: str) -> None:
        self._password.setText(password)

    def _toggle_password(self, checked: bool) -> None:
        self._password.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        self._show_btn.setText(tr("Hide") if checked else tr("Show"))

    def _reset_password_visibility(self) -> None:
        self._show_btn.blockSignals(True)
        self._show_btn.setChecked(False)
        self._show_btn.blockSignals(False)
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._show_btn.setText(tr("Show"))

    def _update_strength(self) -> None:
        password = self._password.text()
        score, label = _estimate_password_strength(password)
        tone = _strength_tone(score)
        self._strength_bar.setValue(score)
        if getattr(self, "_strength_tone", None) != tone:
            self._strength_tone = tone
            set_widget_tone(self._strength_bar, tone)
            set_widget_tone(self._strength_label, tone)
        self._strength_label.setText(label)

    def _copy_password(self) -> None:
        self.copy_password_requested.emit(self._password.text())

    def _emit_save(self) -> None:
        if not self._entry_uuid:
            return
        tags = tuple(
            part.strip()
            for part in self._tags.text().split(",")
            if part.strip()
        )
        expiry_iso = ""
        if self._has_expiry.isChecked():
            expiry_iso = self._expiry_date.date().toString(Qt.DateFormat.ISODate)
        self.save_requested.emit(
            {
                "uuid": self._entry_uuid,
                "title": self._title.text(),
                "username": self._username.text(),
                "password": self._password.text(),
                "url": self._url.text(),
                "notes": self._notes.toPlainText(),
                "custom_properties": self._custom_as_dict(),
                "tags": tags,
                "expires": self._has_expiry.isChecked(),
                "expiry_time": expiry_iso,
            }
        )
