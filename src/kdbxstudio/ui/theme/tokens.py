"""Design tokens for built-in theme styles.

Includes Studio (brand) light/dark plus widely used community palettes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum


class ThemeMode(StrEnum):
    SYSTEM = "system"
    DARK = "dark"
    LIGHT = "light"
    NORD = "nord"
    DRACULA = "dracula"
    TOKYO_NIGHT = "tokyo-night"
    CATPPUCCIN_MOCHA = "catppuccin-mocha"
    CATPPUCCIN_LATTE = "catppuccin-latte"
    SOLARIZED_DARK = "solarized-dark"
    ONE_DARK = "one-dark"
    GRUVBOX_DARK = "gruvbox-dark"
    HIGH_CONTRAST = "high-contrast"
    HIGH_CONTRAST_LIGHT = "high-contrast-light"
    CUSTOM = "custom"


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
    ThemeMode.HIGH_CONTRAST: "High Contrast",
    ThemeMode.HIGH_CONTRAST_LIGHT: "High Contrast Light",
    ThemeMode.CUSTOM: "Custom",
}


@dataclass(frozen=True)
class ThemeTokens:
    mode: ThemeMode
    appearance: str
    brand_primary: str
    brand_primary_hover: str
    brand_accent: str
    brand_on_primary: str
    surface_app: str
    surface_panel: str
    surface_elevated: str
    surface_sunken: str
    surface_overlay: str
    border_subtle: str
    border_strong: str
    border_focus: str
    text_primary: str
    text_secondary: str
    text_muted: str
    text_disabled: str
    text_danger: str
    text_warning: str
    text_success: str
    text_info: str
    focus_ring: str
    shadow_sm: str
    shadow_md: str

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
    surface_overlay: str = "",
    border_subtle: str,
    border_strong: str,
    border_focus: str = "",
    text_primary: str,
    text_secondary: str,
    text_muted: str,
    text_disabled: str = "",
    text_danger: str,
    text_warning: str,
    text_success: str,
    text_info: str = "",
    focus_ring: str | None = None,
    shadow_sm: str = "",
    shadow_md: str = "",
) -> ThemeTokens:
    if not surface_overlay:
        surface_overlay = _blend(surface_elevated, 0.7)
    if not border_focus:
        border_focus = brand_primary
    if not text_disabled:
        text_disabled = _blend(text_primary, 0.3)
    if not text_info:
        text_info = brand_primary
    if not shadow_sm:
        shadow_sm = "0 1px 3px rgba(0,0,0,0.28)"
    if not shadow_md:
        shadow_md = "0 8px 24px rgba(0,0,0,0.40)"
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
        surface_overlay=surface_overlay,
        border_subtle=border_subtle,
        border_strong=border_strong,
        border_focus=border_focus,
        text_primary=text_primary,
        text_secondary=text_secondary,
        text_muted=text_muted,
        text_disabled=text_disabled,
        text_danger=text_danger,
        text_warning=text_warning,
        text_success=text_success,
        text_info=text_info,
        focus_ring=focus_ring or brand_primary,
        shadow_sm=shadow_sm,
        shadow_md=shadow_md,
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
    surface_overlay: str = "",
    border_subtle: str,
    border_strong: str,
    border_focus: str = "",
    text_primary: str,
    text_secondary: str,
    text_muted: str,
    text_disabled: str = "",
    text_danger: str,
    text_warning: str,
    text_success: str,
    text_info: str = "",
    focus_ring: str | None = None,
    shadow_sm: str = "",
    shadow_md: str = "",
) -> ThemeTokens:
    if not surface_overlay:
        surface_overlay = _blend(surface_elevated, 0.85)
    if not border_focus:
        border_focus = brand_primary
    if not text_disabled:
        text_disabled = _blend(text_primary, 0.35)
    if not text_info:
        text_info = brand_primary
    if not shadow_sm:
        shadow_sm = "0 1px 3px rgba(0,0,0,0.06)"
    if not shadow_md:
        shadow_md = "0 8px 24px rgba(0,0,0,0.10)"
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
        surface_overlay=surface_overlay,
        border_subtle=border_subtle,
        border_strong=border_strong,
        border_focus=border_focus,
        text_primary=text_primary,
        text_secondary=text_secondary,
        text_muted=text_muted,
        text_disabled=text_disabled,
        text_danger=text_danger,
        text_warning=text_warning,
        text_success=text_success,
        text_info=text_info,
        focus_ring=focus_ring or brand_primary,
        shadow_sm=shadow_sm,
        shadow_md=shadow_md,
    )


def _blend(hex_color: str, factor: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Brand defaults ──────────────────────────────────────────────────────────

STUDIO_LIGHT = _light(
    ThemeMode.LIGHT,
    brand_primary="#2563EB",
    brand_primary_hover="#1D4ED8",
    brand_accent="#7C3AED",
    brand_on_primary="#FFFFFF",
    surface_app="#F8FAFC",
    surface_panel="#FFFFFF",
    surface_elevated="#F1F5F9",
    surface_sunken="#F1F5F9",
    border_subtle="#E2E8F0",
    border_strong="#CBD5E1",
    text_primary="#0F172A",
    text_secondary="#475569",
    text_muted="#94A3B8",
    text_danger="#DC2626",
    text_warning="#D97706",
    text_success="#059669",
    focus_ring="#2563EB",
)

STUDIO_DARK = _dark(
    ThemeMode.DARK,
    brand_primary="#60A5FA",
    brand_primary_hover="#93C5FD",
    brand_accent="#A78BFA",
    brand_on_primary="#0F172A",
    surface_app="#0F1117",
    surface_panel="#161B22",
    surface_elevated="#1C2128",
    surface_sunken="#0D1117",
    surface_overlay="#1C2128E0",
    border_subtle="#21262D",
    border_strong="#30363D",
    border_focus="#60A5FA",
    text_primary="#E6EDF3",
    text_secondary="#8B949E",
    text_muted="#6E7681",
    text_disabled="#484F58",
    text_danger="#F85149",
    text_warning="#D29922",
    text_success="#3FB950",
    text_info="#58A6FF",
    focus_ring="#60A5FA",
)

# ── Community palettes ──────────────────────────────────────────────────────

NORD = _dark(
    ThemeMode.NORD,
    brand_primary="#88C0D0",
    brand_primary_hover="#8FBCBB",
    brand_accent="#B48EAD",
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
    surface_app="#11111B",
    surface_panel="#1E1E2E",
    surface_elevated="#313244",
    surface_sunken="#181825",
    border_subtle="#313244",
    border_strong="#45475A",
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
    border_strong="#BCC0CC",
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
    brand_accent="#D3869B",
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
    text_warning="#FABD2F",
    text_success="#B8BB26",
)

HIGH_CONTRAST = _dark(
    ThemeMode.HIGH_CONTRAST,
    brand_primary="#00E5FF",
    brand_primary_hover="#66F0FF",
    brand_accent="#FFFF00",
    brand_on_primary="#000000",
    surface_app="#000000",
    surface_panel="#0A0A0A",
    surface_elevated="#1A1A1A",
    surface_sunken="#000000",
    border_subtle="#FFFFFF",
    border_strong="#FFFFFF",
    text_primary="#FFFFFF",
    text_secondary="#FFFFFF",
    text_muted="#CCCCCC",
    text_danger="#FF5555",
    text_warning="#FFDD00",
    text_success="#00FF88",
)

HIGH_CONTRAST_LIGHT = _light(
    ThemeMode.HIGH_CONTRAST_LIGHT,
    brand_primary="#0000EE",
    brand_primary_hover="#0000AA",
    brand_accent="#AA0000",
    brand_on_primary="#FFFFFF",
    surface_app="#FFFFFF",
    surface_panel="#FFFFFF",
    surface_elevated="#F0F0F0",
    surface_sunken="#EEEEEE",
    border_subtle="#000000",
    border_strong="#000000",
    text_primary="#000000",
    text_secondary="#000000",
    text_muted="#333333",
    text_danger="#CC0000",
    text_warning="#886600",
    text_success="#006600",
)

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
    ThemeMode.HIGH_CONTRAST: HIGH_CONTRAST,
    ThemeMode.HIGH_CONTRAST_LIGHT: HIGH_CONTRAST_LIGHT,
}

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
    ThemeMode.HIGH_CONTRAST,
    ThemeMode.HIGH_CONTRAST_LIGHT,
    ThemeMode.CUSTOM,
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
    if mode == ThemeMode.SYSTEM:
        return STUDIO_DARK
    if mode == ThemeMode.CUSTOM:
        from kdbxstudio.ui.theme.custom_theme import current_custom_tokens

        custom = current_custom_tokens()
        if custom is not None:
            return custom
        return replace(STUDIO_DARK, mode=ThemeMode.CUSTOM)
    return THEME_REGISTRY.get(mode, STUDIO_DARK)
