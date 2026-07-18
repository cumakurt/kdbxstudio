"""Apply and resolve application themes."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QGuiApplication, QPalette, QScreen
from PySide6.QtWidgets import QApplication, QWidget

from kdbxstudio.ui.theme.scale import UiScale, detect_ui_scale
from kdbxstudio.ui.theme.styles import build_stylesheet
from kdbxstudio.ui.theme.tokens import (
    ThemeMode,
    ThemeTokens,
    parse_theme,
    tokens_for,
)

_current_scale: UiScale = UiScale(1.0)
_current_mode: ThemeMode = ThemeMode.DARK
_preferred_mode: ThemeMode = ThemeMode.DARK
_current_tokens: ThemeTokens = tokens_for(ThemeMode.DARK)
_theme_applied: bool = False
_scheme_hooked: bool = False


def current_ui_scale() -> UiScale:
    return _current_scale


def current_tokens() -> ThemeTokens:
    """Tokens for the last applied (resolved) theme."""
    return _current_tokens


def preferred_mode() -> ThemeMode:
    """User preference, which may be SYSTEM."""
    return _preferred_mode


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
    preferred = parse_theme(mode)
    if preferred == ThemeMode.SYSTEM:
        return detect_system_mode()
    return preferred


def _qcolor(hex_color: str) -> QColor:
    return QColor(hex_color)


def build_palette(tokens: ThemeTokens) -> QPalette:
    """Map design tokens onto a QPalette for native / unstyled widgets."""
    palette = QPalette()
    window = _qcolor(tokens.surface_app)
    panel = _qcolor(tokens.surface_panel)
    elevated = _qcolor(tokens.surface_elevated)
    sunken = _qcolor(tokens.surface_sunken)
    text = _qcolor(tokens.text_primary)
    secondary = _qcolor(tokens.text_secondary)
    muted = _qcolor(tokens.text_muted)
    brand = _qcolor(tokens.brand_primary)
    on_brand = _qcolor(tokens.brand_on_primary)
    danger = _qcolor(tokens.text_danger)

    palette.setColor(QPalette.ColorRole.Window, window)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, sunken)
    palette.setColor(QPalette.ColorRole.AlternateBase, panel)
    palette.setColor(QPalette.ColorRole.ToolTipBase, elevated)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, elevated)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, danger)
    palette.setColor(QPalette.ColorRole.Highlight, brand)
    palette.setColor(QPalette.ColorRole.HighlightedText, on_brand)
    palette.setColor(QPalette.ColorRole.Link, brand)
    palette.setColor(QPalette.ColorRole.LinkVisited, brand)
    palette.setColor(QPalette.ColorRole.PlaceholderText, muted)
    palette.setColor(QPalette.ColorRole.Light, elevated)
    palette.setColor(QPalette.ColorRole.Midlight, panel)
    palette.setColor(QPalette.ColorRole.Dark, sunken)
    palette.setColor(QPalette.ColorRole.Mid, _qcolor(tokens.border_strong))
    palette.setColor(QPalette.ColorRole.Shadow, _qcolor(tokens.border_subtle))

    for group in (QPalette.ColorGroup.Disabled, QPalette.ColorGroup.Inactive):
        palette.setColor(group, QPalette.ColorRole.WindowText, secondary)
        palette.setColor(group, QPalette.ColorRole.Text, muted)
        palette.setColor(group, QPalette.ColorRole.ButtonText, muted)
        palette.setColor(group, QPalette.ColorRole.Highlight, _qcolor(tokens.border_strong))
        palette.setColor(group, QPalette.ColorRole.HighlightedText, text)

    return palette


def set_widget_tone(widget: QWidget, tone: str | None) -> None:
    """Set a QSS ``tone`` dynamic property and force a style refresh."""
    value = tone or ""
    if widget.property("tone") == value:
        return
    widget.setProperty("tone", value)
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def apply_theme(
    app: QApplication,
    mode: ThemeMode | str,
    *,
    scale: UiScale | None = None,
    screen: QScreen | None = None,
    force: bool = False,
) -> ThemeTokens:
    global _current_scale, _current_mode, _preferred_mode, _current_tokens, _theme_applied
    preferred = parse_theme(mode)
    resolved = resolve_mode(preferred)
    ui_scale = scale if scale is not None else detect_ui_scale(screen)
    if (
        not force
        and _theme_applied
        and resolved == _current_mode
        and preferred == _preferred_mode
        and abs(ui_scale.factor - _current_scale.factor) < 0.01
    ):
        return _current_tokens
    _preferred_mode = preferred
    _theme_applied = True
    _current_mode = resolved
    _current_scale = ui_scale
    tokens = tokens_for(resolved)
    _current_tokens = tokens
    app.setPalette(build_palette(tokens))
    app.setStyleSheet(build_stylesheet(tokens, ui_scale))
    font = QFont("Inter")
    if not font.exactMatch():
        font = QFont("Noto Sans")
    font.setPixelSize(ui_scale.font_px(11))
    app.setFont(font)
    _ensure_system_scheme_hook(app)
    return tokens


def _ensure_system_scheme_hook(app: QApplication) -> None:
    global _scheme_hooked
    if _scheme_hooked:
        return
    hints = app.styleHints()
    try:
        hints.colorSchemeChanged.connect(_on_system_scheme_changed)
        _scheme_hooked = True
    except (AttributeError, TypeError):
        pass


def _on_system_scheme_changed(*_args: object) -> None:
    if _preferred_mode != ThemeMode.SYSTEM:
        return
    app = QApplication.instance()
    if isinstance(app, QApplication):
        apply_theme(app, ThemeMode.SYSTEM)


def refresh_theme_for_screen(screen: QScreen | None = None) -> ThemeTokens | None:
    """Re-apply the active theme using the given (or primary) screen scale."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return None
    return apply_theme(app, _preferred_mode, screen=screen)
