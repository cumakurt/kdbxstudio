"""Theme package."""

from kdbxstudio.ui.theme.manager import (
    apply_theme,
    current_ui_scale,
    refresh_theme_for_screen,
    resolve_mode,
)
from kdbxstudio.ui.theme.scale import UiScale, detect_ui_scale, suggested_window_size
from kdbxstudio.ui.theme.tokens import ThemeMode, ThemeTokens, tokens_for

__all__ = [
    "ThemeMode",
    "ThemeTokens",
    "UiScale",
    "apply_theme",
    "current_ui_scale",
    "detect_ui_scale",
    "refresh_theme_for_screen",
    "resolve_mode",
    "suggested_window_size",
    "tokens_for",
]
