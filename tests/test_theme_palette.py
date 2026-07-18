"""Theme token / scale / palette unit tests."""

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QLabel

from kdbxstudio.ui.dialogs.command_palette import PaletteAction, score_action
from kdbxstudio.ui.theme.manager import (
    apply_theme,
    build_palette,
    current_tokens,
    set_widget_tone,
)
from kdbxstudio.ui.theme.scale import UiScale, detect_ui_scale
from kdbxstudio.ui.theme.styles import build_stylesheet
from kdbxstudio.ui.theme.tokens import (
    THEME_CHOICES,
    THEME_REGISTRY,
    ThemeMode,
    parse_theme,
    theme_label,
    tokens_for,
)


def test_tokens_light_dark_differ() -> None:
    light = tokens_for(ThemeMode.LIGHT)
    dark = tokens_for(ThemeMode.DARK)
    assert light.surface_app != dark.surface_app
    assert light.brand_primary.startswith("#")
    assert light.text_danger != dark.text_danger
    assert light.is_dark is False
    assert dark.is_dark is True
    # Light elevation must step above panel so chrome/cards read depth.
    assert light.surface_elevated != light.surface_panel
    assert light.surface_app != light.surface_panel


def test_stylesheet_has_pane_depth_hooks() -> None:
    css = build_stylesheet(tokens_for(ThemeMode.DARK))
    assert "QWidget#workspaceChrome" in css
    assert "QTableView#entryListPane" in css
    assert "QTabWidget#entryDetailPane::pane" in css
    assert "QSplitter::handle:horizontal" in css
    assert "width: 4px" in css


def test_at_least_five_named_styles() -> None:
    # System is not a palette; named styles must include brand + community themes.
    named = [m for m in THEME_CHOICES if m != ThemeMode.SYSTEM]
    assert len(named) >= 5
    assert len(THEME_REGISTRY) >= 5
    for mode in named:
        tokens = tokens_for(mode)
        assert tokens.mode == mode
        assert tokens.surface_app.startswith("#")
        assert tokens.brand_primary.startswith("#")
        assert theme_label(mode)


def test_community_themes_have_distinct_surfaces() -> None:
    surfaces = {tokens_for(m).surface_app for m in THEME_REGISTRY}
    assert len(surfaces) >= 8


def test_parse_theme_accepts_aliases_and_unknown() -> None:
    assert parse_theme("nord") == ThemeMode.NORD
    assert parse_theme("tokyo-night") == ThemeMode.TOKYO_NIGHT
    assert parse_theme("bogus") == ThemeMode.DARK
    assert parse_theme(ThemeMode.DRACULA) == ThemeMode.DRACULA


def test_stylesheet_contains_brand() -> None:
    css = build_stylesheet(tokens_for(ThemeMode.DARK))
    assert "#3D9A9C" in css
    assert "font-size: 13px" in css
    assert "border-radius: 8px" in css


def test_stylesheet_covers_item_views_and_tones() -> None:
    dark = build_stylesheet(tokens_for(ThemeMode.DARK))
    light = build_stylesheet(tokens_for(ThemeMode.LIGHT))
    for css in (dark, light):
        assert "QTableView" in css
        assert "QTreeView" in css
        assert "QTextBrowser" in css
        assert "QCalendarWidget QWidget#qt_calendar_navigationbar" in css
        assert "QDateEdit::drop-down" in css
        assert "QRadioButton" in css
        assert "QScrollBar:horizontal" in css
        assert 'QProgressBar[tone="success"]' in css
        assert 'QLabel[tone="danger"]' in css
    assert tokens_for(ThemeMode.LIGHT).surface_app in light
    assert tokens_for(ThemeMode.DARK).surface_app in dark


def test_nord_stylesheet_uses_nord_colors() -> None:
    css = build_stylesheet(tokens_for(ThemeMode.NORD))
    assert "#2E3440" in css
    assert "#88C0D0" in css


def test_stylesheet_scales_with_ui_factor() -> None:
    css = build_stylesheet(tokens_for(ThemeMode.DARK), UiScale(1.0))
    assert "font-size: 13px" in css


def test_ui_scale_px_helpers() -> None:
    scale = UiScale(1.0)
    assert scale.px(8) == 8
    assert scale.font_px(11) == 11
    assert scale.factor == 1.0


def test_detect_ui_scale_is_baseline() -> None:
    scale = detect_ui_scale(None)
    assert isinstance(scale, UiScale)
    assert scale.factor == 1.0


def test_palette_score() -> None:
    action = PaletteAction("save", "Save Database", ("save", "disk"), lambda: None)
    assert score_action(action, "save") >= 50
    assert score_action(action, "xyz") == 0


def test_build_palette_maps_surfaces() -> None:
    tokens = tokens_for(ThemeMode.LIGHT)
    palette = build_palette(tokens)
    assert palette.color(QPalette.ColorRole.Window).name().lower() == tokens.surface_app.lower()
    assert palette.color(QPalette.ColorRole.Text).name().lower() == tokens.text_primary.lower()
    assert (
        palette.color(QPalette.ColorRole.Highlight).name().lower()
        == tokens.brand_primary.lower()
    )


def test_apply_theme_switches_styles(qtbot) -> None:
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    apply_theme(app, ThemeMode.LIGHT, force=True)
    assert current_tokens().mode == ThemeMode.LIGHT
    assert tokens_for(ThemeMode.LIGHT).surface_app in app.styleSheet()
    apply_theme(app, ThemeMode.DRACULA, force=True)
    assert current_tokens().mode == ThemeMode.DRACULA
    assert tokens_for(ThemeMode.DRACULA).surface_app in app.styleSheet()
    apply_theme(app, ThemeMode.TOKYO_NIGHT, force=True)
    assert current_tokens().mode == ThemeMode.TOKYO_NIGHT


def test_set_widget_tone(qtbot) -> None:
    label = QLabel("x")
    qtbot.addWidget(label)
    set_widget_tone(label, "danger")
    assert label.property("tone") == "danger"
    set_widget_tone(label, "success")
    assert label.property("tone") == "success"


def test_studio_accent_overlays_primary() -> None:
    from kdbxstudio.ui.theme.accent import apply_accent, parse_accent

    dark = tokens_for(ThemeMode.DARK)
    blue = apply_accent(dark, "blue")
    assert blue.brand_primary == "#5B8DEF"
    assert blue.focus_ring == "#5B8DEF"
    # Accent retints brand colors on community themes too (surfaces stay).
    nord = apply_accent(tokens_for(ThemeMode.NORD), "blue")
    assert nord.brand_primary == "#5B8DEF"
    assert nord.surface_app == tokens_for(ThemeMode.NORD).surface_app
    assert parse_accent("bogus").value == "teal"


def test_density_changes_control_height_in_qss() -> None:
    compact = build_stylesheet(tokens_for(ThemeMode.DARK), ui_density="compact")
    comfort = build_stylesheet(tokens_for(ThemeMode.DARK), ui_density="comfortable")
    assert "min-height: 24px" in compact or "min-height: 28px" in compact
    assert compact != comfort


def test_font_size_and_menu_size_affect_stylesheet() -> None:
    from kdbxstudio.ui.theme.scale import ui_scale_from_percent

    small = build_stylesheet(
        tokens_for(ThemeMode.DARK),
        ui_scale_from_percent(100),
        font_size=11,
        menu_size="small",
    )
    large = build_stylesheet(
        tokens_for(ThemeMode.DARK),
        ui_scale_from_percent(125),
        font_size=16,
        menu_size="large",
    )
    assert "font-size: 11px" in small
    assert "font-size: 20px" in large or "font-size: 16px" in large
    assert small != large


def test_ui_scale_from_percent() -> None:
    from kdbxstudio.ui.theme.scale import ui_scale_from_percent

    assert ui_scale_from_percent(100).factor == 1.0
    assert abs(ui_scale_from_percent(150).factor - 1.5) < 0.001
    assert ui_scale_from_percent(150).px(10) == 15
    assert abs(ui_scale_from_percent(40).factor - 0.4) < 0.001
    assert ui_scale_from_percent(40).px(10) == 4


def test_window_resolution_presets() -> None:
    from kdbxstudio.ui.theme.geometry import (
        normalize_window_resolution,
        window_size_for_resolution,
    )

    assert normalize_window_resolution("1920x1080") == "1920x1080"
    assert window_size_for_resolution("auto") is None
    assert window_size_for_resolution("1280x800") == (1280, 800)


def test_icon_registry_paints(qtbot) -> None:
    from kdbxstudio.ui.icons import icon, known_icons

    assert len(known_icons()) >= 40
    assert not icon("lock", size=20).isNull()
    assert not icon("dashboard", size=18).isNull()
