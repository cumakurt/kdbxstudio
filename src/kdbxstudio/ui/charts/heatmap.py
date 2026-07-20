"""Simple risk heat / severity matrix."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QPaintEvent
from PySide6.QtWidgets import QSizePolicy, QWidget

from kdbxstudio.ui.charts._paint import chart_colors, draw_panel_background


class HeatMapWidget(QWidget):
    """1×N severity cells (Critical / High / Medium / Low)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("securityHeatMap")
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._cells: list[tuple[str, int, str]] = []

    def set_cells(
        self, cells: list[tuple[str, int, str]] | tuple[tuple[str, int, str], ...]
    ) -> None:
        """cells: (label, count, tone) where tone is danger|warning|success|brand."""
        self._cells = list(cells)
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw_panel_background(painter, self)
        colors = chart_colors(self)
        if not self._cells:
            painter.setPen(colors["muted"])
            painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), "No risks")
            return

        tone_map = {
            "danger": colors["danger"],
            "warning": colors["warning"],
            "success": colors["success"],
            "brand": colors["brand"],
            "critical": colors["danger"],
            "high": colors["warning"],
            "medium": colors["brand"],
            "low": colors["success"],
        }
        n = len(self._cells)
        gap = 8
        margin = 12
        cell_w = (self.width() - 2 * margin - gap * (n - 1)) // n
        cell_h = self.height() - 2 * margin
        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(16)
        label_font = QFont(painter.font())
        label_font.setPointSize(9)

        for index, (label, count, tone) in enumerate(self._cells):
            x = margin + index * (cell_w + gap)
            color = tone_map.get(tone, colors["brand"])
            fill = color
            fill.setAlpha(40)
            painter.fillRect(x, margin, cell_w, cell_h, fill)
            painter.setPen(color)
            painter.drawRect(x, margin, cell_w - 1, cell_h - 1)
            painter.setFont(font)
            painter.drawText(
                x,
                margin,
                cell_w,
                cell_h // 2 + 8,
                int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom),
                str(count),
            )
            painter.setFont(label_font)
            painter.setPen(colors["secondary"])
            painter.drawText(
                x,
                margin + cell_h // 2,
                cell_w,
                cell_h // 2,
                int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop),
                label,
            )
