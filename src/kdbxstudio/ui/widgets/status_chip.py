"""Compact tone-colored status chip (expiry, tags, badges)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from kdbxstudio.ui.theme.manager import set_widget_tone


class StatusChip(QLabel):
    """Small pill label styled via QSS objectName + tone property."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        object_name: str = "statusChip",
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setVisible(False)
        set_widget_tone(self, "")

    def set_chip(self, text: str, tone: str) -> None:
        self.setText(text)
        set_widget_tone(self, tone)
        self.setVisible(bool(text))

    def clear_chip(self) -> None:
        self.clear()
        set_widget_tone(self, "")
        self.setVisible(False)
