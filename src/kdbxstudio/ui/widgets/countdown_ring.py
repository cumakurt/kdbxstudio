"""Circular countdown ring for TOTP and entropy meters."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from kdbxstudio.ui.theme.manager import current_tokens


class CountdownRing(QWidget):
    """Theme-aware circular progress ring with centered caption."""

    def __init__(self, parent: QWidget | None = None, *, size: int = 56) -> None:
        super().__init__(parent)
        self._value = 0
        self._maximum = 30
        self._caption = ""
        self._tone = "accent"
        self.setFixedSize(size, size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_range(self, maximum: int) -> None:
        self._maximum = max(1, int(maximum))
        self.update()

    def set_value(self, value: int) -> None:
        self._value = max(0, min(self._maximum, int(value)))
        self.update()

    def set_caption(self, caption: str) -> None:
        self._caption = caption
        self.update()

    def set_tone(self, tone: str) -> None:
        self._tone = tone or "accent"
        self.update()

    def _accent_color(self) -> QColor:
        tokens = current_tokens()
        if self._tone == "danger":
            return QColor(tokens.text_danger)
        if self._tone == "warning":
            return QColor(tokens.text_warning)
        if self._tone == "success":
            return QColor(tokens.text_success)
        return QColor(tokens.brand_primary)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tokens = current_tokens()
        track = QColor(tokens.border_subtle)
        accent = self._accent_color()

        margin = 4
        rect = QRectF(
            margin,
            margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin,
        )
        pen_w = max(3, self.width() // 12)

        track_pen = QPen(track)
        track_pen.setWidth(pen_w)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        ratio = self._value / float(self._maximum) if self._maximum else 0.0
        arc_pen = QPen(accent)
        arc_pen.setWidth(pen_w)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        span = int(360 * ratio * 16)
        painter.drawArc(rect, 90 * 16, -span)

        painter.setPen(QColor(tokens.text_primary))
        font = QFont(painter.font())
        font.setPixelSize(max(9, self.width() // 4))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), self._caption)
