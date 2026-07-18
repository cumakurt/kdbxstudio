"""Theme-aware painting helpers for chart widgets."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from kdbxstudio.ui.theme.manager import current_tokens


def chart_colors(widget: QWidget | None = None) -> dict[str, QColor]:
    tokens = current_tokens()
    return {
        "bg": QColor(tokens.surface_panel),
        "elevated": QColor(tokens.surface_elevated),
        "text": QColor(tokens.text_primary),
        "muted": QColor(tokens.text_muted),
        "secondary": QColor(tokens.text_secondary),
        "brand": QColor(tokens.brand_primary),
        "success": QColor(tokens.text_success),
        "warning": QColor(tokens.text_warning),
        "danger": QColor(tokens.text_danger),
        "border": QColor(tokens.border_subtle),
    }


def series_palette() -> list[QColor]:
    """Brand-safe series colors (teal / blue / green / orange / cyan / amber)."""
    c = chart_colors()
    return [
        c["brand"],
        QColor("#2563EB"),  # blue
        c["success"],
        QColor("#EA580C"),  # orange
        QColor("#0891B2"),  # cyan
        QColor("#D97706"),  # amber
        c["warning"],
        c["danger"],
        QColor("#0D9488"),  # teal
        QColor("#65A30D"),  # lime green
    ]


def draw_panel_background(painter: QPainter, widget: QWidget) -> None:
    colors = chart_colors(widget)
    painter.fillRect(widget.rect(), colors["bg"])
    pen = QPen(colors["border"])
    pen.setWidth(1)
    painter.setPen(pen)
    painter.drawRect(widget.rect().adjusted(0, 0, -1, -1))
