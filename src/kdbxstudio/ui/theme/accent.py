"""Studio accent overlay for user-selectable brand colors.

Accent applies only to Studio Dark / Studio Light (including System → Studio).
Community palettes keep their baked-in brand colors.
"""

from __future__ import annotations

from dataclasses import replace
from enum import StrEnum

from kdbxstudio.ui.theme.tokens import ThemeMode, ThemeTokens


class AccentId(StrEnum):
    TEAL = "teal"
    BLUE = "blue"
    PURPLE = "purple"
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"


ACCENT_LABELS: dict[AccentId, str] = {
    AccentId.TEAL: "Teal",
    AccentId.BLUE: "Blue",
    AccentId.PURPLE: "Purple",
    AccentId.GREEN: "Green",
    AccentId.ORANGE: "Orange",
    AccentId.RED: "Red",
}

ACCENT_CHOICES: tuple[AccentId, ...] = (
    AccentId.TEAL,
    AccentId.BLUE,
    AccentId.PURPLE,
    AccentId.GREEN,
    AccentId.ORANGE,
    AccentId.RED,
)

# dark_primary, dark_hover, light_primary, light_hover, on_dark, on_light
_ACCENT_COLORS: dict[AccentId, tuple[str, str, str, str, str, str]] = {
    AccentId.TEAL: ("#3D9A9C", "#5CB3B5", "#1A5C5E", "#0F3D3E", "#0A1F20", "#FFFFFF"),
    AccentId.BLUE: ("#5B8DEF", "#7AA3F5", "#2563EB", "#1D4ED8", "#0A1628", "#FFFFFF"),
    AccentId.PURPLE: ("#A78BFA", "#C4B5FD", "#7C3AED", "#6D28D9", "#1A1028", "#FFFFFF"),
    AccentId.GREEN: ("#34D399", "#6EE7B7", "#059669", "#047857", "#0A1F18", "#FFFFFF"),
    AccentId.ORANGE: ("#FB923C", "#FDBA74", "#EA580C", "#C2410C", "#1F1208", "#FFFFFF"),
    AccentId.RED: ("#F87171", "#FCA5A5", "#DC2626", "#B91C1C", "#1F0A0A", "#FFFFFF"),
}

VALID_ACCENT_IDS: frozenset[str] = frozenset(a.value for a in ACCENT_CHOICES)

# Kept for callers that still branch on Studio vs community appearance.
STUDIO_MODES: frozenset[ThemeMode] = frozenset({ThemeMode.DARK, ThemeMode.LIGHT})


def parse_accent(value: str | AccentId | None) -> AccentId:
    if isinstance(value, AccentId):
        return value
    text = (value or "").strip().lower()
    try:
        return AccentId(text)
    except ValueError:
        return AccentId.TEAL


def accent_label(accent: AccentId) -> str:
    return ACCENT_LABELS.get(accent, accent.value)


def accent_swatch(accent: AccentId, *, dark: bool = True) -> str:
    """Return the primary hex used for settings swatches."""
    dark_p, _, light_p, _, _, _ = _ACCENT_COLORS[accent]
    return dark_p if dark else light_p


def apply_accent(tokens: ThemeTokens, accent: AccentId | str | None) -> ThemeTokens:
    """Overlay brand primary/hover/focus for the active palette.

    Surfaces stay theme-specific; accent always retints interactive brand colors
    so View → Accent / Settings swatches produce a visible change on every theme.
    """
    aid = parse_accent(accent)
    dark_p, dark_h, light_p, light_h, on_dark, on_light = _ACCENT_COLORS[aid]
    if tokens.is_dark:
        return replace(
            tokens,
            brand_primary=dark_p,
            brand_primary_hover=dark_h,
            brand_on_primary=on_dark,
            focus_ring=dark_p,
        )
    return replace(
        tokens,
        brand_primary=light_p,
        brand_primary_hover=light_h,
        brand_on_primary=on_light,
        focus_ring=light_p,
    )
