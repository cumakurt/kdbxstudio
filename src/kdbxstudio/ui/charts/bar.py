"""Horizontal / vertical bar chart (histogram)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from kdbxstudio.ui.charts._paint import (
    chart_colors,
    draw_panel_background,
    series_palette,
)


class BarChartWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("securityBarChart")
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._bars: list[tuple[str, int]] = []
        self._horizontal = False

    def set_bars(
        self,
        bars: list[tuple[str, int]] | tuple[tuple[str, int], ...],
        *,
        horizontal: bool = False,
    ) -> None:
        self._bars = [(str(n), max(0, int(v))) for n, v in bars]
        self._horizontal = horizontal
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw_panel_background(painter, self)
        colors = chart_colors(self)
        if not self._bars:
            painter.setPen(colors["muted"])
            painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), "No data")
            return

        palette = series_palette()
        max_v = max((v for _, v in self._bars), default=1) or 1
        margin_l, margin_r, margin_t, margin_b = 8, 8, 12, 28
        plot_w = self.width() - margin_l - margin_r
        plot_h = self.height() - margin_t - margin_b
        n = len(self._bars)
        gap = 6
        font = QFont(painter.font())
        font.setPointSize(8)
        painter.setFont(font)

        if self._horizontal:
            bar_h = max(8, (plot_h - gap * (n - 1)) // n)
            for index, (name, value) in enumerate(self._bars):
                y = margin_t + index * (bar_h + gap)
                w = int(plot_w * 0.55 * (value / max_v))
                painter.fillRect(
                    margin_l + 70,
                    y,
                    max(2, w),
                    bar_h,
                    palette[index % len(palette)],
                )
                painter.setPen(colors["secondary"])
                painter.drawText(
                    margin_l,
                    y,
                    66,
                    bar_h,
                    int(Qt.AlignmentFlag.AlignVCenter),
                    name,
                )
                painter.setPen(colors["text"])
                painter.drawText(
                    margin_l + 70 + max(2, w) + 4,
                    y,
                    40,
                    bar_h,
                    int(Qt.AlignmentFlag.AlignVCenter),
                    str(value),
                )
            return

        bar_w = max(8, (plot_w - gap * (n - 1)) // n)
        for index, (name, value) in enumerate(self._bars):
            x = margin_l + index * (bar_w + gap)
            h = int(plot_h * (value / max_v))
            y = margin_t + plot_h - h
            painter.fillRect(x, y, bar_w, max(2, h), palette[index % len(palette)])
            painter.setPen(colors["text"])
            painter.drawText(
                x,
                y - 14,
                bar_w,
                12,
                int(Qt.AlignmentFlag.AlignHCenter),
                str(value),
            )
            painter.setPen(colors["muted"])
            painter.drawText(
                x - 4,
                self.height() - 22,
                bar_w + 8,
                18,
                int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop),
                name,
            )
