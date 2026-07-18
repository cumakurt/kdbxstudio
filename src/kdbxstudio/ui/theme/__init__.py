"""Theme package."""

from kdbxstudio.ui.theme.manager import (
    apply_theme,
    build_palette,
    current_tokens,
    current_ui_scale,
    preferred_mode,
    refresh_theme_for_screen,
    resolve_mode,
    set_widget_tone,
)
from kdbxstudio.ui.theme.scale import UiScale, detect_ui_scale, suggested_window_size
from kdbxstudio.ui.theme.tokens import (
    THEME_CHOICES,
    ThemeMode,
    ThemeTokens,
    parse_theme,
    theme_label,
    tokens_for,
)

__all__ = [
    "THEME_CHOICES",
    "ThemeMode",
    "ThemeTokens",
    "UiScale",
    "apply_theme",
    "build_palette",
    "current_tokens",
    "current_ui_scale",
    "detect_ui_scale",
    "parse_theme",
    "preferred_mode",
    "refresh_theme_for_screen",
    "resolve_mode",
    "set_widget_tone",
    "suggested_window_size",
    "theme_label",
    "tokens_for",
]
