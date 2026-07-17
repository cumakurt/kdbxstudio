"""Tests for settings persistence and inverted-index search."""

from pathlib import Path

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.search_engine import EntryFilter, SearchEngine, tokenize
from kdbxstudio.security.settings import SecuritySettings
from kdbxstudio.security.store import load_settings, save_settings


def test_settings_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    original = SecuritySettings(
        clipboard_timeout_ms=20_000,
        auto_lock_timeout_ms=120_000,
        auto_lock_enabled=False,
        clear_clipboard_on_lock=False,
        theme="light",
        read_only=True,
    )
    save_settings(original, path)
    loaded = load_settings(path)
    assert loaded == original


def test_load_missing_settings(tmp_path: Path) -> None:
    assert load_settings(tmp_path / "missing.json") == SecuritySettings()


def test_tokenize() -> None:
    assert tokenize("Hello, HTTPS://Example!") == ["hello", "https", "example"]


def test_inverted_index_and_filters(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "idx.kdbx", password="secret")
    root = mgr.root_group_uuid()
    mgr.add_entry(root, title="GitHub Login", username="dev", url="https://github.com")
    mgr.add_entry(root, title="Bank", password="123", notes="weak account")
    api = mgr.add_entry(root, title="API", password="samepass99")
    mgr.update_entry(api.uuid, custom_properties={"Type": "API"})
    mgr.add_entry(root, title="Clone", password="samepass99")

    engine = SearchEngine(mgr)
    hits = engine.search("github")
    assert len(hits) == 1
    assert hits[0].entry.title == "GitHub Login"
    assert "title" in hits[0].matched_fields

    multi = engine.search("github login")
    assert len(multi) == 1

    weak = engine.search("", entry_filter=EntryFilter(weak_only=True))
    assert any(h.entry.title == "Bank" for h in weak)

    dupes = engine.search("", entry_filter=EntryFilter(duplicates_only=True))
    titles = {h.entry.title for h in dupes}
    assert "API" in titles and "Clone" in titles

    custom = engine.search("", entry_filter=EntryFilter(has_otp_or_custom=True))
    assert any(h.entry.title == "API" for h in custom)
