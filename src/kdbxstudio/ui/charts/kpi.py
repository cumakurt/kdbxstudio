"""KPI metric card."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from kdbxstudio.ui.theme.manager import set_widget_tone


class KpiCard(QWidget):
    """Compact title / value / subtitle card."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("securityKpiCard")
        self.setMinimumHeight(88)
        self._title = QLabel(title)
        self._title.setObjectName("securityKpiTitle")
        self._value = QLabel("—")
        self._value.setObjectName("securityKpiValue")
        self._value.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._subtitle = QLabel("")
        self._subtitle.setObjectName("securityKpiSubtitle")
        self._subtitle.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._subtitle)
        layout.addStretch(1)

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def set_value(self, value: str, *, tone: str = "") -> None:
        self._value.setText(value)
        if tone:
            set_widget_tone(self._value, tone)

    def set_subtitle(self, text: str) -> None:
        self._subtitle.setText(text)
        self._subtitle.setVisible(bool(text))
