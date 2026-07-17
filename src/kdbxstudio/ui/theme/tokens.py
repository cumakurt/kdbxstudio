"""Design tokens for light and dark themes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ThemeMode(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass(frozen=True)
class ThemeTokens:
    mode: ThemeMode
    brand_primary: str
    brand_primary_hover: str
    brand_accent: str
    brand_on_primary: str
    surface_app: str
    surface_panel: str
    surface_elevated: str
    surface_sunken: str
    border_subtle: str
    border_strong: str
    text_primary: str
    text_secondary: str
    text_muted: str
    text_danger: str
    text_warning: str
    text_success: str
    focus_ring: str


LIGHT = ThemeTokens(
    mode=ThemeMode.LIGHT,
    brand_primary="#1A5C5E",
    brand_primary_hover="#0F3D3E",
    brand_accent="#C9A227",
    brand_on_primary="#FFFFFF",
    surface_app="#F4F7F7",
    surface_panel="#FFFFFF",
    surface_elevated="#FFFFFF",
    surface_sunken="#E8EEEE",
    border_subtle="#D0DADB",
    border_strong="#A8B8B8",
    text_primary="#142222",
    text_secondary="#4A5C5C",
    text_muted="#7A8C8C",
    text_danger="#B42318",
    text_warning="#B54708",
    text_success="#027A48",
    focus_ring="#1A5C5E",
)

DARK = ThemeTokens(
    mode=ThemeMode.DARK,
    brand_primary="#3D9A9C",
    brand_primary_hover="#5CB3B5",
    brand_accent="#E8C547",
    brand_on_primary="#0A1F20",
    surface_app="#0E1616",
    surface_panel="#152020",
    surface_elevated="#1C2A2A",
    surface_sunken="#0A1212",
    border_subtle="#2A3A3A",
    border_strong="#3D5050",
    text_primary="#E8F0F0",
    text_secondary="#9BB0B0",
    text_muted="#6A8080",
    text_danger="#F97066",
    text_warning="#FDB022",
    text_success="#32D583",
    focus_ring="#3D9A9C",
)


def tokens_for(mode: ThemeMode) -> ThemeTokens:
    if mode == ThemeMode.LIGHT:
        return LIGHT
    return DARK
