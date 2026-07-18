"""Stable hash colors for entry tag chips."""

from __future__ import annotations

import hashlib

from PySide6.QtGui import QColor

from kdbxstudio.ui.theme.manager import current_tokens

# Fixed hues mixed with theme surfaces for readable chips.
_TAG_HUES = (190, 210, 160, 30, 280, 320, 50, 120, 240, 10)


def tag_chip_colors(tag: str) -> tuple[str, str]:
    """Return (background_hex, foreground_hex) for a tag label."""
    digest = hashlib.sha256(tag.strip().lower().encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(_TAG_HUES)
    hue = _TAG_HUES[idx]
    tokens = current_tokens()
    bg = QColor()
    if tokens.is_dark:
        bg.setHsv(hue, 90, 70)
    else:
        bg.setHsv(hue, 70, 230)
    fg = QColor(tokens.text_primary)
    return bg.name(), fg.name()
