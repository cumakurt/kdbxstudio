"""Visual polish helpers: expiry chips, custom theme, tags, calendar QSS."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from kdbxstudio.application.expiry import (
    entry_list_tone,
    expiry_chip_info,
)
from kdbxstudio.core.database import EntryView
from kdbxstudio.ui.theme.custom_theme import clear_custom_tokens, load_custom_theme_json
from kdbxstudio.ui.theme.styles import build_stylesheet
from kdbxstudio.ui.theme.tokens import ThemeMode, tokens_for
from kdbxstudio.ui.widgets.tag_colors import tag_chip_colors


def _entry(**kwargs) -> EntryView:
    base = dict(
        uuid="u1",
        title="t",
        username="u",
        password="",
        url="",
        notes="",
        group_path="Root",
    )
    base.update(kwargs)
    return EntryView(**base)


def test_expiry_chip_tones() -> None:
    past = datetime.now(UTC) - timedelta(days=3)
    expired = _entry(expires=True, expiry_time=past.isoformat())
    info = expiry_chip_info(expired)
    assert info is not None
    assert info.tone == "danger"
    assert "ago" in info.label

    soon = datetime.now(UTC) + timedelta(days=5)
    warning = _entry(expires=True, expiry_time=soon.isoformat())
    info2 = expiry_chip_info(warning)
    assert info2 is not None
    assert info2.tone == "warning"


def test_entry_list_tone_recycle_and_audit() -> None:
    recycled = _entry(in_recycle_bin=True)
    assert entry_list_tone(recycled) == "muted"
    assert entry_list_tone(_entry(), audit_tone="danger") == "danger"


def test_tag_chip_colors_stable() -> None:
    a1, b1 = tag_chip_colors("banking")
    a2, b2 = tag_chip_colors("banking")
    assert a1 == a2
    assert a1.startswith("#")


def test_custom_theme_json_roundtrip(tmp_path: Path) -> None:
    clear_custom_tokens()
    dark = tokens_for(ThemeMode.DARK)
    payload = {
        "appearance": "dark",
        "brand_primary": dark.brand_primary,
        "brand_primary_hover": dark.brand_primary_hover,
        "brand_accent": dark.brand_accent,
        "brand_on_primary": dark.brand_on_primary,
        "surface_app": "#111111",
        "surface_panel": "#222222",
        "surface_elevated": "#333333",
        "surface_sunken": "#0a0a0a",
        "border_subtle": "#444444",
        "border_strong": "#555555",
        "text_primary": "#eeeeee",
        "text_secondary": "#cccccc",
        "text_muted": "#999999",
        "text_danger": "#ff5555",
        "text_warning": "#ffaa00",
        "text_success": "#55ff55",
    }
    path = tmp_path / "theme.json"
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")
    tokens = load_custom_theme_json(path)
    assert tokens.mode == ThemeMode.CUSTOM
    assert tokens.surface_app == "#111111"
    assert tokens_for(ThemeMode.CUSTOM).surface_app == "#111111"
    clear_custom_tokens()


def test_calendar_qss_selectors() -> None:
    css = build_stylesheet(tokens_for(ThemeMode.DARK))
    assert "QCalendarWidget QWidget#qt_calendar_navigationbar" in css
    assert "QDateEdit::drop-down" in css
    assert "QLabel#expiryChip" in css
    assert "QLabel#toastBanner" in css


def test_high_contrast_themes_exist() -> None:
    assert tokens_for(ThemeMode.HIGH_CONTRAST).is_dark
    assert not tokens_for(ThemeMode.HIGH_CONTRAST_LIGHT).is_dark
