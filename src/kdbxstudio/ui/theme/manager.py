"""Apply and resolve application themes."""

from __future__ import annotations

from PySide6.QtGui import QFont, QGuiApplication, QScreen
from PySide6.QtWidgets import QApplication

from kdbxstudio.ui.theme.scale import UiScale, detect_ui_scale
from kdbxstudio.ui.theme.styles import build_stylesheet
from kdbxstudio.ui.theme.tokens import ThemeMode, ThemeTokens, tokens_for

_current_scale: UiScale = UiScale(1.0)
_current_mode: ThemeMode = ThemeMode.DARK
_theme_applied: bool = False


def current_ui_scale() -> UiScale:
    return _current_scale


def detect_system_mode() -> ThemeMode:
    app = QGuiApplication.instance()
    if not isinstance(app, QGuiApplication):
        return ThemeMode.DARK
    hints = app.styleHints()
    try:
        scheme = hints.colorScheme()
        from PySide6.QtCore import Qt

        if scheme == Qt.ColorScheme.Light:
            return ThemeMode.LIGHT
        if scheme == Qt.ColorScheme.Dark:
            return ThemeMode.DARK
    except Exception:
        pass
    return ThemeMode.DARK


def resolve_mode(mode: ThemeMode | str) -> ThemeMode:
    if isinstance(mode, str):
        mode = ThemeMode(mode)
    if mode == ThemeMode.SYSTEM:
        return detect_system_mode()
    return mode


def apply_theme(
    app: QApplication,
    mode: ThemeMode | str,
    *,
    scale: UiScale | None = None,
    screen: QScreen | None = None,
) -> ThemeTokens:
    global _current_scale, _current_mode, _theme_applied
    resolved = resolve_mode(mode)
    ui_scale = scale if scale is not None else detect_ui_scale(screen)
    if (
        _theme_applied
        and resolved == _current_mode
        and abs(ui_scale.factor - _current_scale.factor) < 0.01
    ):
        return tokens_for(resolved)
    _theme_applied = True
    _current_mode = resolved
    _current_scale = ui_scale
    tokens = tokens_for(resolved)
    app.setStyleSheet(build_stylesheet(tokens, ui_scale))
    font = QFont("Inter")
    if not font.exactMatch():
        font = QFont("Noto Sans")
    font.setPixelSize(ui_scale.font_px(11))
    app.setFont(font)
    return tokens


def refresh_theme_for_screen(screen: QScreen | None = None) -> ThemeTokens | None:
    """Re-apply the active theme using the given (or primary) screen scale."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return None
    return apply_theme(app, _current_mode, screen=screen)
