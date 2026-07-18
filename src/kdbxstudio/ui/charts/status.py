"""Status badge and recommendation timeline list."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.ui.theme.manager import set_widget_tone


class StatusBadge(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("securityStatusBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(22)

    def set_status(self, text: str, *, tone: str = "brand") -> None:
        self.setText(text)
        set_widget_tone(self, tone)


class TimelineList(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("securityTimeline")
        self._list = QListWidget()
        self._list.setObjectName("securityTimelineList")
        self._list.setAlternatingRowColors(True)
        self._list.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list)

    def set_items(self, items: list[str] | tuple[str, ...]) -> None:
        self._list.clear()
        for text in items:
            self._list.addItem(QListWidgetItem(f"• {text}"))

    @property
    def list_widget(self) -> QListWidget:
        return self._list
