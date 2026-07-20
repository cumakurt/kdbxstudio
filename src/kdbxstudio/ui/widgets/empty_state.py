"""Reusable empty-state placeholder."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from kdbxstudio.ui.icons import icon


class EmptyStateWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        icon_name: str = "search",
        title: str = "",
        hint: str = "",
    ) -> None:
        super().__init__(parent)
        self.setObjectName("emptyState")
        self._icon = QLabel()
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title = QLabel(title)
        self._title.setObjectName("emptyStateTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setWordWrap(True)
        self._hint = QLabel(hint)
        self._hint.setObjectName("emptyStateHint")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.addWidget(self._icon)
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        self.set_content(title, hint, icon_name=icon_name)

    def set_content(
        self, title: str, hint: str = "", *, icon_name: str | None = None
    ) -> None:
        if icon_name:
            self._icon.setPixmap(icon(icon_name, size=40, brand=True).pixmap(40, 40))
        self._title.setText(title)
        self._hint.setText(hint)
        self._hint.setVisible(bool(hint))
