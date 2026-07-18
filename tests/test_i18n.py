"""Tests for UI language support."""

from __future__ import annotations

from pathlib import Path

from kdbxstudio.i18n import get_language, set_language, tr
from kdbxstudio.security.settings import SecuritySettings
from kdbxstudio.security.store import load_settings, save_settings


def test_default_language_is_english() -> None:
    set_language("en")
    assert get_language() == "en"
    assert tr("Settings") == "Settings"
    assert tr("Open…") == "Open…"


def test_turkish_translations() -> None:
    set_language("tr")
    assert get_language() == "tr"
    assert tr("Settings") == "Ayarlar"
    assert tr("Open…") == "Aç…"
    assert tr("Never expires") == "Süresi dolmaz"
    assert tr("Unknown key that is missing") == "Unknown key that is missing"
    set_language("en")


def test_language_persisted_in_settings(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    save_settings(SecuritySettings(language="tr"), path=path)
    loaded = load_settings(path=path)
    assert loaded.language == "tr"
    save_settings(SecuritySettings(language="en"), path=path)
    assert load_settings(path=path).language == "en"


def test_normalize_invalid_language_falls_back_to_en() -> None:
    assert set_language("de") == "en"
    assert set_language("TR") == "tr"
    set_language("en")
