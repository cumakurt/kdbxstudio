"""Design tokens for built-in theme styles.

Includes Studio (brand) light/dark plus widely used community palettes:
Nord, Dracula, Tokyo Night, Catppuccin, Solarized, One Dark, Gruvbox.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ThemeMode(StrEnum):
    """Persisted theme preference (includes SYSTEM + named styles)."""

    SYSTEM = "system"
    DARK = "dark"  # Studio Dark (default brand)
    LIGHT = "light"  # Studio Light
    NORD = "nord"
    DRACULA = "dracula"
    TOKYO_NIGHT = "tokyo-night"
    CATPPUCCIN_MOCHA = "catppuccin-mocha"
    CATPPUCCIN_LATTE = "catppuccin-latte"
    SOLARIZED_DARK = "solarized-dark"
    ONE_DARK = "one-dark"
    GRUVBOX_DARK = "gruvbox-dark"


# Human-readable English labels (also used as i18n keys via tr()).
THEME_LABELS: dict[ThemeMode, str] = {
    ThemeMode.SYSTEM: "System",
    ThemeMode.DARK: "Studio Dark",
    ThemeMode.LIGHT: "Studio Light",
    ThemeMode.NORD: "Nord",
    ThemeMode.DRACULA: "Dracula",
    ThemeMode.TOKYO_NIGHT: "Tokyo Night",
    ThemeMode.CATPPUCCIN_MOCHA: "Catppuccin Mocha",
    ThemeMode.CATPPUCCIN_LATTE: "Catppuccin Latte",
    ThemeMode.SOLARIZED_DARK: "Solarized Dark",
    ThemeMode.ONE_DARK: "One Dark",
    ThemeMode.GRUVBOX_DARK: "Gruvbox Dark",
}


@dataclass(frozen=True)
class ThemeTokens:
    mode: ThemeMode
    appearance: str  # "light" | "dark" — semantic brightness for SYSTEM resolve
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

    @property
    def is_dark(self) -> bool:
        return self.appearance == "dark"


def _dark(
    mode: ThemeMode,
    *,
    brand_primary: str,
    brand_primary_hover: str,
    brand_accent: str,
    brand_on_primary: str,
    surface_app: str,
    surface_panel: str,
    surface_elevated: str,
    surface_sunken: str,
    border_subtle: str,
    border_strong: str,
    text_primary: str,
    text_secondary: str,
    text_muted: str,
    text_danger: str,
    text_warning: str,
    text_success: str,
    focus_ring: str | None = None,
) -> ThemeTokens:
    return ThemeTokens(
        mode=mode,
        appearance="dark",
        brand_primary=brand_primary,
        brand_primary_hover=brand_primary_hover,
        brand_accent=brand_accent,
        brand_on_primary=brand_on_primary,
        surface_app=surface_app,
        surface_panel=surface_panel,
        surface_elevated=surface_elevated,
        surface_sunken=surface_sunken,
        border_subtle=border_subtle,
        border_strong=border_strong,
        text_primary=text_primary,
        text_secondary=text_secondary,
        text_muted=text_muted,
        text_danger=text_danger,
        text_warning=text_warning,
        text_success=text_success,
        focus_ring=focus_ring or brand_primary,
    )


def _light(
    mode: ThemeMode,
    *,
    brand_primary: str,
    brand_primary_hover: str,
    brand_accent: str,
    brand_on_primary: str,
    surface_app: str,
    surface_panel: str,
    surface_elevated: str,
    surface_sunken: str,
    border_subtle: str,
    border_strong: str,
    text_primary: str,
    text_secondary: str,
    text_muted: str,
    text_danger: str,
    text_warning: str,
    text_success: str,
    focus_ring: str | None = None,
) -> ThemeTokens:
    return ThemeTokens(
        mode=mode,
        appearance="light",
        brand_primary=brand_primary,
        brand_primary_hover=brand_primary_hover,
        brand_accent=brand_accent,
        brand_on_primary=brand_on_primary,
        surface_app=surface_app,
        surface_panel=surface_panel,
        surface_elevated=surface_elevated,
        surface_sunken=surface_sunken,
        border_subtle=border_subtle,
        border_strong=border_strong,
        text_primary=text_primary,
        text_secondary=text_secondary,
        text_muted=text_muted,
        text_danger=text_danger,
        text_warning=text_warning,
        text_success=text_success,
        focus_ring=focus_ring or brand_primary,
    )


# ── Brand defaults ──────────────────────────────────────────────────────────

STUDIO_LIGHT = _light(
    ThemeMode.LIGHT,
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
)

STUDIO_DARK = _dark(
    ThemeMode.DARK,
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
)

# ── Community palettes (official / well-known hex values) ───────────────────

NORD = _dark(
    ThemeMode.NORD,
    brand_primary="#88C0D0",
    brand_primary_hover="#8FBCBB",
    brand_accent="#EBCB8B",
    brand_on_primary="#2E3440",
    surface_app="#2E3440",
    surface_panel="#3B4252",
    surface_elevated="#434C5E",
    surface_sunken="#242933",
    border_subtle="#4C566A",
    border_strong="#5E6A7E",
    text_primary="#ECEFF4",
    text_secondary="#D8DEE9",
    text_muted="#7B88A1",
    text_danger="#BF616A",
    text_warning="#D08770",
    text_success="#A3BE8C",
)

DRACULA = _dark(
    ThemeMode.DRACULA,
    brand_primary="#BD93F9",
    brand_primary_hover="#D6ACFF",
    brand_accent="#FF79C6",
    brand_on_primary="#282A36",
    surface_app="#282A36",
    surface_panel="#2F3244",
    surface_elevated="#44475A",
    surface_sunken="#21222C",
    border_subtle="#44475A",
    border_strong="#6272A4",
    text_primary="#F8F8F2",
    text_secondary="#BFBFB8",
    text_muted="#6272A4",
    text_danger="#FF5555",
    text_warning="#FFB86C",
    text_success="#50FA7B",
)

TOKYO_NIGHT = _dark(
    ThemeMode.TOKYO_NIGHT,
    brand_primary="#7AA2F7",
    brand_primary_hover="#89B4FA",
    brand_accent="#BB9AF7",
    brand_on_primary="#1A1B26",
    surface_app="#1A1B26",
    surface_panel="#1F2335",
    surface_elevated="#292E42",
    surface_sunken="#16161E",
    border_subtle="#3B4261",
    border_strong="#565F89",
    text_primary="#C0CAF5",
    text_secondary="#A9B1D6",
    text_muted="#565F89",
    text_danger="#F7768E",
    text_warning="#E0AF68",
    text_success="#9ECE6A",
)

CATPPUCCIN_MOCHA = _dark(
    ThemeMode.CATPPUCCIN_MOCHA,
    brand_primary="#89B4FA",
    brand_primary_hover="#B4BEFE",
    brand_accent="#CBA6F7",
    brand_on_primary="#1E1E2E",
    surface_app="#1E1E2E",
    surface_panel="#181825",
    surface_elevated="#313244",
    surface_sunken="#11111B",
    border_subtle="#45475A",
    border_strong="#585B70",
    text_primary="#CDD6F4",
    text_secondary="#A6ADC8",
    text_muted="#6C7086",
    text_danger="#F38BA8",
    text_warning="#FAB387",
    text_success="#A6E3A1",
)

CATPPUCCIN_LATTE = _light(
    ThemeMode.CATPPUCCIN_LATTE,
    brand_primary="#1E66F5",
    brand_primary_hover="#1A56D6",
    brand_accent="#8839EF",
    brand_on_primary="#FFFFFF",
    surface_app="#EFF1F5",
    surface_panel="#FFFFFF",
    surface_elevated="#FFFFFF",
    surface_sunken="#E6E9EF",
    border_subtle="#CCD0DA",
    border_strong="#9CA0B0",
    text_primary="#4C4F69",
    text_secondary="#5C5F77",
    text_muted="#8C8FA1",
    text_danger="#D20F39",
    text_warning="#FE640B",
    text_success="#40A02B",
)

SOLARIZED_DARK = _dark(
    ThemeMode.SOLARIZED_DARK,
    brand_primary="#268BD2",
    brand_primary_hover="#2AA198",
    brand_accent="#B58900",
    brand_on_primary="#002B36",
    surface_app="#002B36",
    surface_panel="#073642",
    surface_elevated="#0A4150",
    surface_sunken="#00212B",
    border_subtle="#586E75",
    border_strong="#657B83",
    text_primary="#839496",
    text_secondary="#93A1A1",
    text_muted="#586E75",
    text_danger="#DC322F",
    text_warning="#CB4B16",
    text_success="#859900",
)

ONE_DARK = _dark(
    ThemeMode.ONE_DARK,
    brand_primary="#61AFEF",
    brand_primary_hover="#528BCC",
    brand_accent="#C678DD",
    brand_on_primary="#282C34",
    surface_app="#21252B",
    surface_panel="#282C34",
    surface_elevated="#2C313A",
    surface_sunken="#1B1F23",
    border_subtle="#3E4451",
    border_strong="#4B5263",
    text_primary="#ABB2BF",
    text_secondary="#9DA5B4",
    text_muted="#5C6370",
    text_danger="#E06C75",
    text_warning="#E5C07B",
    text_success="#98C379",
)

GRUVBOX_DARK = _dark(
    ThemeMode.GRUVBOX_DARK,
    brand_primary="#83A598",
    brand_primary_hover="#8EC07C",
    brand_accent="#FABD2F",
    brand_on_primary="#282828",
    surface_app="#1D2021",
    surface_panel="#282828",
    surface_elevated="#3C3836",
    surface_sunken="#161819",
    border_subtle="#504945",
    border_strong="#665C54",
    text_primary="#EBDBB2",
    text_secondary="#D5C4A1",
    text_muted="#928374",
    text_danger="#FB4934",
    text_warning="#FE8019",
    text_success="#B8BB26",
)

# Backward-compatible aliases
LIGHT = STUDIO_LIGHT
DARK = STUDIO_DARK

THEME_REGISTRY: dict[ThemeMode, ThemeTokens] = {
    ThemeMode.DARK: STUDIO_DARK,
    ThemeMode.LIGHT: STUDIO_LIGHT,
    ThemeMode.NORD: NORD,
    ThemeMode.DRACULA: DRACULA,
    ThemeMode.TOKYO_NIGHT: TOKYO_NIGHT,
    ThemeMode.CATPPUCCIN_MOCHA: CATPPUCCIN_MOCHA,
    ThemeMode.CATPPUCCIN_LATTE: CATPPUCCIN_LATTE,
    ThemeMode.SOLARIZED_DARK: SOLARIZED_DARK,
    ThemeMode.ONE_DARK: ONE_DARK,
    ThemeMode.GRUVBOX_DARK: GRUVBOX_DARK,
}

# Order shown in Settings / View → Theme menus
THEME_CHOICES: tuple[ThemeMode, ...] = (
    ThemeMode.SYSTEM,
    ThemeMode.DARK,
    ThemeMode.LIGHT,
    ThemeMode.NORD,
    ThemeMode.DRACULA,
    ThemeMode.TOKYO_NIGHT,
    ThemeMode.CATPPUCCIN_MOCHA,
    ThemeMode.CATPPUCCIN_LATTE,
    ThemeMode.SOLARIZED_DARK,
    ThemeMode.ONE_DARK,
    ThemeMode.GRUVBOX_DARK,
)

VALID_THEME_IDS: frozenset[str] = frozenset(m.value for m in THEME_CHOICES)


def parse_theme(value: str | ThemeMode | None) -> ThemeMode:
    if isinstance(value, ThemeMode):
        return value
    text = (value or "").strip().lower()
    try:
        return ThemeMode(text)
    except ValueError:
        return ThemeMode.DARK


def theme_label(mode: ThemeMode) -> str:
    return THEME_LABELS.get(mode, mode.value)


def tokens_for(mode: ThemeMode) -> ThemeTokens:
    """Return tokens for a concrete (non-SYSTEM) theme."""
    if mode == ThemeMode.SYSTEM:
        return STUDIO_DARK
    return THEME_REGISTRY.get(mode, STUDIO_DARK)
