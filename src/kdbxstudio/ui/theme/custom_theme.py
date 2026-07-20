"""Load user-imported JSON theme tokens."""

from __future__ import annotations

import json
import re
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

_optional_fields = {
    "surface_overlay": "",
    "border_focus": "",
    "text_disabled": "",
    "text_info": "",
    "focus_ring": "",
    "shadow_sm": "",
    "shadow_md": "",
}

_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{5})?$")

_custom_tokens: ThemeTokens | None = None


def current_custom_tokens() -> ThemeTokens | None:
    return _custom_tokens


def clear_custom_tokens() -> None:
    global _custom_tokens
    _custom_tokens = None


def load_custom_theme_json(path: Path | str) -> ThemeTokens:
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
        if not _COLOR_RE.fullmatch(value):
            raise ValueError(f"Invalid color for {key}: {value}")

    opt_values = {}
    for key, default in _optional_fields.items():
        opt_values[key] = str(data.get(key, default) or default)
        if key not in {"shadow_sm", "shadow_md"} and opt_values[key]:
            if not _COLOR_RE.fullmatch(opt_values[key]):
                raise ValueError(f"Invalid color for {key}: {opt_values[key]}")

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
        surface_overlay=opt_values["surface_overlay"] or data["surface_elevated"],
        border_subtle=str(data["border_subtle"]),
        border_strong=str(data["border_strong"]),
        border_focus=opt_values["border_focus"] or data["brand_primary"],
        text_primary=str(data["text_primary"]),
        text_secondary=str(data["text_secondary"]),
        text_muted=str(data["text_muted"]),
        text_disabled=opt_values["text_disabled"],
        text_danger=str(data["text_danger"]),
        text_warning=str(data["text_warning"]),
        text_success=str(data["text_success"]),
        text_info=opt_values["text_info"] or data["brand_primary"],
        focus_ring=str(opt_values["focus_ring"] or data["brand_primary"]),
        shadow_sm=opt_values["shadow_sm"],
        shadow_md=opt_values["shadow_md"],
    )
    _custom_tokens = tokens
    return tokens
