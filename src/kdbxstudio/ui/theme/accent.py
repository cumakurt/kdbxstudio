"""Studio accent overlay for user-selectable brand colors."""

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

_ACCENT_COLORS: dict[AccentId, tuple[str, str, str, str, str, str]] = {
    AccentId.TEAL: ("#14B8A6", "#2DD4BF", "#0D9488", "#0F766E", "#042F2E", "#FFFFFF"),
    AccentId.BLUE: ("#3B82F6", "#60A5FA", "#2563EB", "#1D4ED8", "#1E3A5F", "#FFFFFF"),
    AccentId.PURPLE: ("#8B5CF6", "#A78BFA", "#7C3AED", "#6D28D9", "#2E1065", "#FFFFFF"),
    AccentId.GREEN: ("#10B981", "#34D399", "#059669", "#047857", "#022C22", "#FFFFFF"),
    AccentId.ORANGE: ("#F59E0B", "#FBBF24", "#D97706", "#B45309", "#431407", "#FFFFFF"),
    AccentId.RED: ("#EF4444", "#F87171", "#DC2626", "#B91C1C", "#450A0A", "#FFFFFF"),
}

VALID_ACCENT_IDS: frozenset[str] = frozenset(a.value for a in ACCENT_CHOICES)

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
    dark_p, _, light_p, _, _, _ = _ACCENT_COLORS[accent]
    return dark_p if dark else light_p


def apply_accent(tokens: ThemeTokens, accent: AccentId | str | None) -> ThemeTokens:
    aid = parse_accent(accent)
    dark_p, dark_h, light_p, light_h, on_dark, on_light = _ACCENT_COLORS[aid]
    if tokens.is_dark:
        return replace(
            tokens,
            brand_primary=dark_p,
            brand_primary_hover=dark_h,
            brand_on_primary=on_dark,
            focus_ring=dark_p,
            border_focus=dark_p,
            text_info=dark_p,
        )
    return replace(
        tokens,
        brand_primary=light_p,
        brand_primary_hover=light_h,
        brand_on_primary=on_light,
        focus_ring=light_p,
        border_focus=light_p,
        text_info=light_p,
    )
