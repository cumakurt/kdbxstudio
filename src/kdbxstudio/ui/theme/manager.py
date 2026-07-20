"""Apply and resolve application themes."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QPalette,
    QScreen,
    QTextCharFormat,
)
from PySide6.QtWidgets import QApplication, QWidget

from kdbxstudio.ui.theme.accent import AccentId, apply_accent, parse_accent
from kdbxstudio.ui.theme.geometry import (
    clamp_font_size,
    clamp_ui_scale_percent,
    normalize_menu_size,
    type_scale_for_body,
)
from kdbxstudio.ui.theme.scale import UiScale, ui_scale_from_percent
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
_current_accent: AccentId = AccentId.TEAL
_current_density: str = "compact"
_current_font_size: int = 13
_current_menu_size: str = "medium"
_current_scale_percent: int = 100
_current_tokens: ThemeTokens = tokens_for(ThemeMode.DARK)
_theme_applied: bool = False
_scheme_hooked: bool = False


def current_ui_scale() -> UiScale:
    return _current_scale


def current_tokens() -> ThemeTokens:
    """Tokens for the last applied (resolved) theme."""
    return _current_tokens


def current_accent() -> AccentId:
    return _current_accent


def current_density() -> str:
    return _current_density


def current_font_size() -> int:
    return _current_font_size


def current_menu_size() -> str:
    return _current_menu_size


def current_ui_scale_percent() -> int:
    return _current_scale_percent


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
        palette.setColor(
            group, QPalette.ColorRole.Highlight, _qcolor(tokens.border_strong)
        )
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


def polish_calendar_popup(date_edit: QWidget) -> None:
    """Force theme palette on a QDateEdit calendar popup when it opens."""
    calendar_fn = getattr(date_edit, "calendarWidget", None)
    if calendar_fn is None:
        return
    calendar = calendar_fn()
    if calendar is None:
        return
    calendar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    calendar.setAutoFillBackground(True)
    calendar.setPalette(build_palette(_current_tokens))

    today_fmt = QTextCharFormat()
    today_fmt.setForeground(_qcolor(_current_tokens.brand_primary))
    today_fmt.setFontWeight(700)
    calendar.setDateTextFormat(QDate.currentDate(), today_fmt)

    weekend = QTextCharFormat()
    weekend.setForeground(_qcolor(_current_tokens.text_muted))
    calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend)
    calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend)


def apply_theme(
    app: QApplication,
    mode: ThemeMode | str,
    *,
    accent: AccentId | str | None = None,
    ui_density: str | None = None,
    ui_scale_percent: int | None = None,
    font_size: int | None = None,
    menu_size: str | None = None,
    scale: UiScale | None = None,
    screen: QScreen | None = None,
    force: bool = False,
) -> ThemeTokens:
    global _current_scale, _current_mode, _preferred_mode, _current_tokens
    global _theme_applied, _current_accent, _current_density
    global _current_font_size, _current_menu_size, _current_scale_percent
    preferred = parse_theme(mode)
    resolved = resolve_mode(preferred)
    accent_id = parse_accent(accent if accent is not None else _current_accent)
    density = (ui_density if ui_density is not None else _current_density) or "compact"
    if density not in ("compact", "comfortable"):
        density = "compact"
    scale_pct = clamp_ui_scale_percent(
        ui_scale_percent if ui_scale_percent is not None else _current_scale_percent
    )
    body_font = clamp_font_size(
        font_size if font_size is not None else _current_font_size
    )
    menu = normalize_menu_size(
        menu_size if menu_size is not None else _current_menu_size
    )
    ui_scale = scale if scale is not None else ui_scale_from_percent(scale_pct)
    if (
        not force
        and _theme_applied
        and resolved == _current_mode
        and preferred == _preferred_mode
        and accent_id == _current_accent
        and density == _current_density
        and body_font == _current_font_size
        and menu == _current_menu_size
        and scale_pct == _current_scale_percent
        and abs(ui_scale.factor - _current_scale.factor) < 0.01
    ):
        return _current_tokens
    _preferred_mode = preferred
    _theme_applied = True
    _current_mode = resolved
    _current_accent = accent_id
    _current_density = density
    _current_font_size = body_font
    _current_menu_size = menu
    _current_scale_percent = scale_pct
    _current_scale = ui_scale
    tokens = apply_accent(tokens_for(resolved), accent_id)
    _current_tokens = tokens
    app.setPalette(build_palette(tokens))
    app.setStyleSheet(
        build_stylesheet(
            tokens,
            ui_scale,
            ui_density=density,
            font_size=body_font,
            menu_size=menu,
        )
    )
    type_scale = type_scale_for_body(body_font)
    font = QFont("Inter")
    if not font.exactMatch():
        font = QFont("Noto Sans")
    font.setPixelSize(ui_scale.font_px(type_scale.body))
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
        apply_theme(
            app,
            ThemeMode.SYSTEM,
            accent=_current_accent,
            ui_density=_current_density,
            ui_scale_percent=_current_scale_percent,
            font_size=_current_font_size,
            menu_size=_current_menu_size,
        )


def refresh_theme_for_screen(screen: QScreen | None = None) -> ThemeTokens | None:
    """Re-apply the active theme using the given (or primary) screen scale."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return None
    return apply_theme(
        app,
        _preferred_mode,
        accent=_current_accent,
        ui_density=_current_density,
        ui_scale_percent=_current_scale_percent,
        font_size=_current_font_size,
        menu_size=_current_menu_size,
        screen=screen,
    )
