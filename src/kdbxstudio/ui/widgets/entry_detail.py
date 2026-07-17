"""Entry detail editor with contextual field icons."""

from __future__ import annotations

import math
import re
from datetime import UTC, datetime

from PySide6.QtCore import QDate, QSize, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.core.database import EntryView
from kdbxstudio.ui.icons.entry_type import (
    EntryKind,
    FieldKind,
    detect_entry_kind,
    field_icon,
)
from kdbxstudio.ui.widgets.notes_preview import NotesPreviewWidget


def _leading_icon(edit: QLineEdit, icon_kind: FieldKind) -> QAction:
    action = QAction(edit)
    action.setIcon(field_icon(icon_kind))
    edit.addAction(action, QLineEdit.ActionPosition.LeadingPosition)
    return action


def _estimate_password_strength(password: str) -> tuple[int, str]:
    """Return (score 0-100, label) for a password."""
    if not password:
        return 0, "Empty"
    score = 0
    length = len(password)
    if length >= 8:
        score += 20
    elif length >= 6:
        score += 10
    if length >= 16:
        score += 20
    elif length >= 12:
        score += 15
    if re.search(r"[a-z]", password):
        score += 10
    if re.search(r"[A-Z]", password):
        score += 10
    if re.search(r"\d", password):
        score += 10
    if re.search(r"[^a-zA-Z0-9]", password):
        score += 15
    unique_chars = len(set(password))
    if unique_chars >= 10:
        score += 10
    elif unique_chars >= 6:
        score += 5
    entropy = len(password) * math.log2(max(1, unique_chars))
    if entropy >= 60:
        score += 10
    elif entropy >= 40:
        score += 5
    score = min(100, score)
    if score >= 80:
        label = "Strong"
    elif score >= 60:
        label = "Good"
    elif score >= 40:
        label = "Fair"
    elif score >= 20:
        label = "Weak"
    else:
        label = "Very Weak"
    return score, label


def _strength_color(score: int) -> str:
    if score >= 80:
        return "#22c55e"
    elif score >= 60:
        return "#84cc16"
    elif score >= 40:
        return "#eab308"
    elif score >= 20:
        return "#f97316"
    return "#ef4444"


class EntryDetailWidget(QWidget):
    """View / edit a single entry."""

    save_requested = Signal(dict)
    copy_password_requested = Signal(str)
    generate_password_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
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
        self._strength_bar.setMaximumHeight(16)
        self._strength_bar.setFormat("")
        self._strength_label = QLabel("")
        self._strength_label.setStyleSheet("font-size: 11px;")
        self._url = QLineEdit()
        self._notes = NotesPreviewWidget()
        self._tags = QLineEdit()
        self._tags.setPlaceholderText("Comma-separated tags")
        self._expires = QCheckBox("Expires")
        self._expiry_date = QDateEdit()
        self._expiry_date.setCalendarPopup(True)
        self._expiry_date.setDisplayFormat("yyyy-MM-dd")
        self._expiry_date.setDate(QDate.currentDate().addYears(1))
        self._expiry_date.setEnabled(False)
        self._expires.toggled.connect(self._expiry_date.setEnabled)

        self._expiry_countdown = QLabel("")
        self._expiry_countdown.setWordWrap(True)
        self._expiry_countdown.setVisible(False)

        expiry_row = QHBoxLayout()
        expiry_row.addWidget(self._expires)
        expiry_row.addWidget(self._expiry_date, stretch=1)

        self._title_icon = _leading_icon(self._title, FieldKind.TITLE)
        self._username_icon = _leading_icon(self._username, FieldKind.USERNAME)
        self._password_icon = _leading_icon(self._password, FieldKind.PASSWORD)
        self._url_icon = _leading_icon(self._url, FieldKind.URL)

        self._title.textChanged.connect(self._refresh_field_icons)
        self._url.textChanged.connect(self._refresh_field_icons)
        self._username.textChanged.connect(self._refresh_field_icons)
        self._password.textChanged.connect(self._update_strength)

        self._custom = QTableWidget(0, 2)
        self._custom.setHorizontalHeaderLabels(["Key", "Value"])
        self._custom.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._custom.verticalHeader().setVisible(False)

        copy_btn = QPushButton("Copy")
        copy_btn.setIcon(field_icon(FieldKind.COPY))
        copy_btn.setIconSize(QSize(14, 14))
        copy_btn.setToolTip("Copy password")
        copy_btn.clicked.connect(self._copy_password)

        self._show_btn = QPushButton("Show")
        self._show_btn.setIcon(field_icon(FieldKind.SHOW))
        self._show_btn.setIconSize(QSize(14, 14))
        self._show_btn.setCheckable(True)
        self._show_btn.toggled.connect(self._toggle_password)

        gen_btn = QPushButton("Generate")
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
        strength_row.addWidget(self._strength_bar, stretch=1)
        strength_row.addWidget(self._strength_label)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.addWidget(self._kind_badge)
        title_row.addWidget(self._title, stretch=1)

        add_prop = QPushButton("Add field")
        add_prop.setIcon(field_icon(FieldKind.CUSTOM))
        add_prop.setIconSize(QSize(14, 14))
        add_prop.clicked.connect(self._add_custom_row)
        del_prop = QPushButton("Remove field")
        del_prop.clicked.connect(self._remove_custom_row)
        prop_btns = QHBoxLayout()
        prop_btns.addWidget(add_prop)
        prop_btns.addWidget(del_prop)
        prop_btns.addStretch()

        form = QFormLayout()
        form.setSpacing(6)
        form.addRow("Title", title_row)
        form.addRow("Username", self._username)
        form.addRow("Password", pwd_row)
        form.addRow("Strength", strength_row)
        form.addRow("URL", self._url)
        form.addRow("Tags", self._tags)
        form.addRow("Expiry", expiry_row)
        form.addRow("", self._expiry_countdown)
        form.addRow("Notes", self._notes)
        form.addRow("Custom fields", self._custom)
        form.addRow("", prop_btns)

        save_btn = QPushButton("Save entry")
        save_btn.setIcon(field_icon(FieldKind.SAVE))
        save_btn.setIconSize(QSize(14, 14))
        save_btn.clicked.connect(self._emit_save)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(form)
        layout.addWidget(save_btn)
        self.set_enabled(False)
        self._apply_kind_icons(EntryKind.GENERIC)

    def set_enabled(self, enabled: bool) -> None:
        for widget in (
            self._title,
            self._username,
            self._password,
            self._url,
            self._tags,
            self._expires,
            self._expiry_date,
            self._notes,
            self._custom,
        ):
            widget.setEnabled(enabled)
        if enabled:
            self._expiry_date.setEnabled(self._expires.isChecked())

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
        self._expires.setChecked(False)
        self._expiry_countdown.setVisible(False)
        self._title.blockSignals(False)
        self._url.blockSignals(False)
        self._username.blockSignals(False)
        self._notes.clear()
        self._custom.setRowCount(0)
        self._apply_kind_icons(EntryKind.GENERIC)
        self.set_enabled(False)

    def load_entry(self, entry: EntryView) -> None:
        self._entry_uuid = entry.uuid
        self._title.blockSignals(True)
        self._url.blockSignals(True)
        self._username.blockSignals(True)
        self._title.setText(entry.title)
        self._username.setText(entry.username)
        self._password.setText(entry.password)
        self._url.setText(entry.url)
        self._tags.setText(", ".join(entry.tags))
        self._expires.setChecked(entry.expires)
        if entry.expiry_time:
            date = QDate.fromString(entry.expiry_time[:10], "yyyy-MM-dd")
            if date.isValid():
                self._expiry_date.setDate(date)
        self._title.blockSignals(False)
        self._url.blockSignals(False)
        self._username.blockSignals(False)
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
        self.set_enabled(True)

    def _update_expiry_countdown(self, entry: EntryView) -> None:
        if not entry.expires or not entry.expiry_time:
            self._expiry_countdown.setVisible(False)
            return
        try:
            text = entry.expiry_time.strip()
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            expiry_dt = datetime.fromisoformat(text)
            if expiry_dt.tzinfo is None:
                expiry_dt = expiry_dt.replace(tzinfo=UTC)
            now = datetime.now(UTC)
            delta = expiry_dt - now
            days = delta.days
            if days < 0:
                self._expiry_countdown.setText(
                    f"⚠ Expired {abs(days)} day(s) ago"
                )
                self._expiry_countdown.setStyleSheet(
                    "color: #ef4444; font-weight: bold;"
                )
            elif days == 0:
                self._expiry_countdown.setText("⚠ Expires today!")
                self._expiry_countdown.setStyleSheet(
                    "color: #f97316; font-weight: bold;"
                )
            elif days <= 7:
                self._expiry_countdown.setText(
                    f"⏰ Expires in {days} day(s)"
                )
                self._expiry_countdown.setStyleSheet(
                    "color: #f97316; font-weight: bold;"
                )
            elif days <= 30:
                self._expiry_countdown.setText(
                    f"📅 Expires in {days} day(s)"
                )
                self._expiry_countdown.setStyleSheet(
                    "color: #eab308;"
                )
            else:
                self._expiry_countdown.setText(
                    f"✓ Expires in {days} day(s)"
                )
                self._expiry_countdown.setStyleSheet(
                    "color: #22c55e;"
                )
            self._expiry_countdown.setVisible(True)
        except (ValueError, TypeError):
            self._expiry_countdown.setVisible(False)

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
        # Password placeholder hint by kind
        hints = {
            EntryKind.API: "API key / token",
            EntryKind.SSH: "Passphrase (optional)",
            EntryKind.BANK: "Card number",
            EntryKind.WIFI: "Wi-Fi password",
            EntryKind.CERTIFICATE: "Key passphrase",
            EntryKind.DATABASE: "Database password",
        }
        self._password.setPlaceholderText(hints.get(kind, "Password"))
        user_hints = {
            EntryKind.EMAIL: "Email address",
            EntryKind.SSH: "SSH user / comment",
            EntryKind.BANK: "Cardholder name",
            EntryKind.API: "Client id (optional)",
        }
        self._username.setPlaceholderText(user_hints.get(kind, "Username"))

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

    def set_password(self, password: str) -> None:
        self._password.setText(password)

    def _toggle_password(self, checked: bool) -> None:
        self._password.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        self._show_btn.setText("Hide" if checked else "Show")

    def _update_strength(self) -> None:
        password = self._password.text()
        score, label = _estimate_password_strength(password)
        color = _strength_color(score)
        self._strength_bar.setValue(score)
        self._strength_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; }}"
        )
        self._strength_label.setText(label)
        self._strength_label.setStyleSheet(
            f"font-size: 11px; color: {color}; font-weight: bold;"
        )

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
        if self._expires.isChecked():
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
                "expires": self._expires.isChecked(),
                "expiry_time": expiry_iso,
            }
        )
