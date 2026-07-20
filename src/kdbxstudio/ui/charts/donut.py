"""Donut chart widget."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from kdbxstudio.ui.charts._paint import (
    chart_colors,
    draw_panel_background,
    series_palette,
)


class DonutChartWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("securityDonut")
        self.setMinimumSize(180, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._slices: list[tuple[str, int]] = []
        self._center = ""

    def set_slices(
        self,
        slices: list[tuple[str, int]] | tuple[tuple[str, int], ...],
        *,
        center: str = "",
    ) -> None:
        self._slices = [(str(n), max(0, int(v))) for n, v in slices if int(v) > 0]
        self._center = center
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw_panel_background(painter, self)
        colors = chart_colors(self)
        total = sum(v for _, v in self._slices) or 1
        palette = series_palette()

        chart_w = min(self.width() - 100, self.height() - 20)
        chart_w = max(80, chart_w)
        rect = QRectF(12, (self.height() - chart_w) / 2, chart_w, chart_w)

        start = 90 * 16
        for index, (_name, value) in enumerate(self._slices):
            span = int(360 * 16 * (value / total))
            pen = QPen(palette[index % len(palette)])
            pen.setWidth(14)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawArc(rect.adjusted(8, 8, -8, -8), start, -span)
            start -= span

        painter.setPen(colors["text"])
        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        center_text = self._center or str(total)
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), center_text)

        # Legend
        lx = rect.right() + 12
        ly = 16.0
        small = QFont(painter.font())
        small.setPointSize(9)
        small.setBold(False)
        painter.setFont(small)
        for index, (name, value) in enumerate(self._slices[:8]):
            color = palette[index % len(palette)]
            painter.fillRect(int(lx), int(ly), 10, 10, color)
            painter.setPen(colors["secondary"])
            painter.drawText(
                int(lx + 14),
                int(ly + 10),
                f"{name}: {value}",
            )
            ly += 16
