"""Theme package."""

from kdbxstudio.ui.theme.accent import (
    ACCENT_CHOICES,
    AccentId,
    accent_label,
    accent_swatch,
    apply_accent,
    parse_accent,
)
from kdbxstudio.ui.theme.manager import (
    apply_theme,
    build_palette,
    current_accent,
    current_density,
    current_tokens,
    current_ui_scale,
    preferred_mode,
    refresh_theme_for_screen,
    resolve_mode,
    set_widget_tone,
)
from kdbxstudio.ui.theme.motion import (
    MotionDuration,
    fade_and_slide_in,
    fade_in,
    slide_in,
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
    "ACCENT_CHOICES",
    "AccentId",
    "MotionDuration",
    "THEME_CHOICES",
    "ThemeMode",
    "ThemeTokens",
    "UiScale",
    "accent_label",
    "accent_swatch",
    "apply_accent",
    "apply_theme",
    "build_palette",
    "current_accent",
    "current_density",
    "current_tokens",
    "current_ui_scale",
    "detect_ui_scale",
    "fade_and_slide_in",
    "fade_in",
    "parse_accent",
    "parse_theme",
    "preferred_mode",
    "refresh_theme_for_screen",
    "resolve_mode",
    "set_widget_tone",
    "slide_in",
    "suggested_window_size",
    "theme_label",
    "tokens_for",
]
