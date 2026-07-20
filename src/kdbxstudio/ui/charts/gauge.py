"""Circular gauge for Security Score."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from kdbxstudio.ui.charts._paint import chart_colors, draw_panel_background


class GaugeWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("securityGauge")
        self.setMinimumSize(160, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._value = 0
        self._label = ""
        self._caption = "Security Score"

    def set_data(self, value: int, label: str = "", caption: str = "") -> None:
        self._value = max(0, min(100, int(value)))
        self._label = label
        if caption:
            self._caption = caption
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw_panel_background(painter, self)
        colors = chart_colors(self)
        if self._value >= 75:
            accent = colors["success"]
        elif self._value >= 50:
            accent = colors["warning"]
        else:
            accent = colors["danger"]

        # Reserve dedicated caption/label bands so text does not overlap the arc
        # at the dashboard's minimum panel height.
        side = min(self.width() - 24, self.height() - 64)
        side = max(40, side)
        cx = self.width() / 2
        cy = self.height() / 2
        rect = QRectF(cx - side / 2, cy - side / 2, side, side)

        track = QPen(colors["border"])
        track.setWidth(10)
        track.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track)
        painter.drawArc(rect, 45 * 16, 270 * 16)

        arc = QPen(accent)
        arc.setWidth(10)
        arc.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc)
        span = int(270 * (self._value / 100.0) * 16)
        painter.drawArc(rect, (45 + 270) * 16 - span, span)

        painter.setPen(colors["text"])
        font = QFont(painter.font())
        font.setPointSize(22)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), f"{self._value}")

        painter.setPen(colors["muted"])
        small = QFont(painter.font())
        small.setPointSize(9)
        small.setBold(False)
        painter.setFont(small)
        caption_rect = QRectF(8, 8, self.width() - 16, 20)
        painter.drawText(
            caption_rect,
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop),
            self._caption,
        )
        if self._label:
            label_rect = QRectF(8, self.height() - 28, self.width() - 16, 20)
            painter.setPen(accent)
            painter.drawText(
                label_rect,
                int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom),
                self._label,
            )
