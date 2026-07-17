"""Theme token / scale / palette unit tests."""

from kdbxstudio.ui.dialogs.command_palette import PaletteAction, score_action
from kdbxstudio.ui.theme.scale import UiScale, detect_ui_scale
from kdbxstudio.ui.theme.styles import build_stylesheet
from kdbxstudio.ui.theme.tokens import ThemeMode, tokens_for


def test_tokens_light_dark_differ() -> None:
    light = tokens_for(ThemeMode.LIGHT)
    dark = tokens_for(ThemeMode.DARK)
    assert light.surface_app != dark.surface_app
    assert light.brand_primary.startswith("#")


def test_stylesheet_contains_brand() -> None:
    css = build_stylesheet(tokens_for(ThemeMode.DARK))
    assert "#3D9A9C" in css
    assert "font-size: 11px" in css
    assert "border-radius: 4px" in css


def test_stylesheet_scales_with_ui_factor() -> None:
    css = build_stylesheet(tokens_for(ThemeMode.DARK), UiScale(1.0))
    assert "font-size: 11px" in css


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
