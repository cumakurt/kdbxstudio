"""Load user-imported JSON theme tokens."""

from __future__ import annotations

import json
from pathlib import Path

from kdbxstudio.ui.theme.tokens import ThemeMode, ThemeTokens

_REQUIRED = (
    "brand_primary",
    "brand_primary_hover",
    "brand_accent",
    "brand_on_primary",
    "surface_app",
    "surface_panel",
    "surface_elevated",
    "surface_sunken",
    "border_subtle",
    "border_strong",
    "text_primary",
    "text_secondary",
    "text_muted",
    "text_danger",
    "text_warning",
    "text_success",
)

_custom_tokens: ThemeTokens | None = None


def current_custom_tokens() -> ThemeTokens | None:
    return _custom_tokens


def clear_custom_tokens() -> None:
    global _custom_tokens
    _custom_tokens = None


def load_custom_theme_json(path: Path | str) -> ThemeTokens:
    """Validate and store a custom theme from JSON; returns tokens."""
    global _custom_tokens
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Theme JSON must be an object")
    missing = [k for k in _REQUIRED if k not in data]
    if missing:
        raise ValueError(f"Missing theme keys: {', '.join(missing)}")
    appearance = str(data.get("appearance", "dark")).lower()
    if appearance not in ("dark", "light"):
        appearance = "dark"
    for key in _REQUIRED:
        value = str(data[key]).strip()
        if not value.startswith("#") or len(value) not in (4, 7, 9):
            raise ValueError(f"Invalid color for {key}: {value}")
    tokens = ThemeTokens(
        mode=ThemeMode.CUSTOM,
        appearance=appearance,
        brand_primary=str(data["brand_primary"]),
        brand_primary_hover=str(data["brand_primary_hover"]),
        brand_accent=str(data["brand_accent"]),
        brand_on_primary=str(data["brand_on_primary"]),
        surface_app=str(data["surface_app"]),
        surface_panel=str(data["surface_panel"]),
        surface_elevated=str(data["surface_elevated"]),
        surface_sunken=str(data["surface_sunken"]),
        border_subtle=str(data["border_subtle"]),
        border_strong=str(data["border_strong"]),
        text_primary=str(data["text_primary"]),
        text_secondary=str(data["text_secondary"]),
        text_muted=str(data["text_muted"]),
        text_danger=str(data["text_danger"]),
        text_warning=str(data["text_warning"]),
        text_success=str(data["text_success"]),
        focus_ring=str(data.get("focus_ring") or data["brand_primary"]),
    )
    _custom_tokens = tokens
    return tokens
