"""Advanced entry filter bar with chip-style toggles."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QWidget,
)

from kdbxstudio.application.expiry import EXPIRING_SOON_DAYS
from kdbxstudio.application.search_engine import EntryFilter
from kdbxstudio.i18n import tr


def _chip(label: str) -> QToolButton:
    button = QToolButton()
    button.setText(label)
    button.setCheckable(True)
    button.setProperty("cssClass", "chip")
    button.setAccessibleName(label)
    button.setToolTip(label)
    return button


class FilterBarWidget(QWidget):
    """Compact advanced filters above the entry list."""

    filter_changed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._group = QLineEdit()
        self._group.setPlaceholderText(tr("Group contains…"))
        self._group.setAccessibleName(tr("Group path filter"))
        self._group.returnPressed.connect(self._emit)

        self._tag = QLineEdit()
        self._tag.setPlaceholderText(tr("Tag…"))
        self._tag.setAccessibleName(tr("Tag filter"))
        self._tag.returnPressed.connect(self._emit)

        self._has_url = _chip(tr("URL"))
        self._has_custom = _chip(tr("Custom/OTP"))
        self._weak = _chip(tr("Weak"))
        self._empty = _chip(tr("Empty"))
        self._dupes = _chip(tr("Dupes"))
        self._expired = _chip(tr("Expired"))
        self._expiring = _chip(tr("Expiring"))
        self._recycle = _chip(tr("Recycle"))

        self._chips = (
            self._has_url,
            self._has_custom,
            self._weak,
            self._empty,
            self._dupes,
            self._expired,
            self._expiring,
            self._recycle,
        )
        for chip, tip in zip(
            self._chips,
            (
                tr("Has URL"),
                tr("Has custom fields or OTP"),
                tr("Weak passwords"),
                tr("Empty passwords"),
                tr("Duplicates"),
                tr("Past expiry date"),
                tr("Expiring within {n} days").format(n=EXPIRING_SOON_DAYS),
                tr("Recycle Bin only"),
            ),
            strict=True,
        ):
            chip.setToolTip(tip)
            chip.setAccessibleName(tip)
            chip.toggled.connect(self._emit)

        apply_btn = QPushButton(tr("Apply"))
        apply_btn.clicked.connect(self._emit)
        clear_btn = QPushButton(tr("Clear"))
        clear_btn.clicked.connect(self.clear)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel(tr("Filter")))
        layout.addWidget(self._group, stretch=1)
        layout.addWidget(self._tag)
        for chip in self._chips:
            layout.addWidget(chip)
        layout.addWidget(apply_btn)
        layout.addWidget(clear_btn)

    def clear(self) -> None:
        self._group.blockSignals(True)
        self._tag.blockSignals(True)
        for chip in self._chips:
            chip.blockSignals(True)
        try:
            self._group.clear()
            self._tag.clear()
            for chip in self._chips:
                chip.setChecked(False)
        finally:
            self._group.blockSignals(False)
            self._tag.blockSignals(False)
            for chip in self._chips:
                chip.blockSignals(False)
        self._emit()

    def current_filter(self, query: str = "") -> EntryFilter:
        return EntryFilter(
            query=query,
            group_path_contains=self._group.text().strip(),
            tag_contains=self._tag.text().strip(),
            has_url=True if self._has_url.isChecked() else None,
            has_otp_or_custom=True if self._has_custom.isChecked() else None,
            in_recycle_bin=True if self._recycle.isChecked() else False,
            weak_only=self._weak.isChecked(),
            empty_password=self._empty.isChecked(),
            duplicates_only=self._dupes.isChecked(),
            expired_only=self._expired.isChecked(),
            expiring_soon_only=self._expiring.isChecked(),
        )

    def _emit(self) -> None:
        self.filter_changed.emit(self.current_filter())
