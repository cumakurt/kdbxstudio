"""Regression tests for code-quality fixes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from kdbxstudio.application.autotype import AutoTypeError, auto_type, expand_sequence
from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.expiry import is_expired, local_date_to_utc_end_of_day
from kdbxstudio.application.import_csv import import_entries_csv
from kdbxstudio.application.merge import merge_databases
from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.application.search_engine import EntryFilter, SearchEngine
from kdbxstudio.core.database import EntryView, KdbxDatabase
from kdbxstudio.plugins.sdk import PluginContext, PluginMeta
from kdbxstudio.security.settings import SecuritySettings
from kdbxstudio.security.store import load_settings, save_settings


def test_bitwarden_style_csv_aliases(tmp_path: Path) -> None:
    db_path = tmp_path / "import.kdbx"
    csv_path = tmp_path / "bw.csv"
    csv_path.write_text(
        "name,login_username,login_password,login_uri,folder,notes\n"
        "Site,ada,secret,https://example.com,Work,hi\n",
        encoding="utf-8",
    )
    db = KdbxDatabase()
    db.create(db_path, password="pass")
    result = import_entries_csv(db, csv_path)
    assert result.created == 1
    entry = next(e for e in db.list_entries() if e.title == "Site")
    assert entry.username == "ada"
    assert entry.password == "secret"
    assert entry.url == "https://example.com"


def test_expired_filter_uses_past_due(tmp_path: Path) -> None:
    path = tmp_path / "exp.kdbx"
    db = KdbxDatabase()
    db.create(path, password="pass")
    root = db.root_group_uuid()
    past = datetime.now(UTC) - timedelta(days=2)
    future = datetime.now(UTC) + timedelta(days=30)
    old = db.add_entry(root, title="Old")
    db.update_entry(old.uuid, expires=True, expiry_time=past)
    fresh = db.add_entry(root, title="Fresh")
    db.update_entry(fresh.uuid, expires=True, expiry_time=future)
    db.save()

    mgr = DatabaseManager()
    mgr.open(path, password="pass")
    engine = SearchEngine(mgr)
    hits = engine.search("", entry_filter=EntryFilter(expired_only=True))
    titles = {h.entry.title for h in hits}
    assert "Old" in titles
    assert "Fresh" not in titles


def test_local_date_end_of_day_is_aware() -> None:
    dt = local_date_to_utc_end_of_day("2030-01-15")
    assert dt.tzinfo is not None


def test_is_expired_helper() -> None:
    entry = EntryView(
        uuid="1",
        title="t",
        username="",
        password="",
        url="",
        notes="",
        group_path="Root",
        expires=True,
        expiry_time=(datetime.now(UTC) - timedelta(days=1)).isoformat(),
    )
    assert is_expired(entry)


def test_settings_round_trip_all_fields(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    original = SecuritySettings(
        clipboard_timeout_ms=12_000,
        auto_lock_timeout_ms=120_000,
        auto_lock_enabled=False,
        clear_clipboard_on_lock=False,
        minimize_on_lock=True,
        theme="light",
        read_only=True,
        window_geometry="abc",
        window_state="def",
        ui_density="comfortable",
        hibp_enabled=True,
        autotype_sequence="{PASSWORD}{ENTER}",
        check_updates_on_start=False,
        start_minimized_to_tray=True,
    )
    save_settings(original, path)
    loaded = load_settings(path)
    assert loaded == original


def test_plugin_reregister_clears_hooks() -> None:
    class Demo:
        meta = PluginMeta(name="demo", version="1")

        def __init__(self) -> None:
            self.calls = 0

        def activate(self, context: PluginContext) -> None:
            def _hook(**_: object) -> int:
                self.calls += 1
                return self.calls

            context.register_hook("ping", _hook, owner=self.meta.name)

        def deactivate(self, context: PluginContext) -> None:
            context.clear_owner(self.meta.name)

    mgr = PluginManager()
    first = Demo()
    mgr.register(first)
    mgr.activate("demo")
    mgr.context.emit("ping")
    second = Demo()
    mgr.register(second)  # should deactivate first
    mgr.activate("demo")
    mgr.context.emit("ping")
    assert first.calls == 1
    assert second.calls == 1


def test_merge_skips_existing_signature(tmp_path: Path) -> None:
    src = KdbxDatabase()
    dst = KdbxDatabase()
    src.create(tmp_path / "s.kdbx", password="a")
    dst.create(tmp_path / "d.kdbx", password="b")
    src.add_entry(src.root_group_uuid(), title="Shared", username="u", password="1")
    dst.add_entry(dst.root_group_uuid(), title="Shared", username="u", password="old")
    result = merge_databases(dst, src)
    assert result.added == 0
    assert result.skipped == 1
    updated = merge_databases(dst, src, update_existing=True)
    assert updated.updated == 1
    entry = next(e for e in dst.list_entries() if e.title == "Shared")
    assert entry.password == "1"


def test_autotype_expand_still_works() -> None:
    assert expand_sequence("{TAB}", username="", password="") == [("key", "Tab")]


def test_autotype_missing_backend_raises(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import kdbxstudio.application.autotype as mod

    monkeypatch.setattr(mod, "detect_backend", lambda: None)
    try:
        auto_type("{PASSWORD}", username="", password="x", initial_delay_ms=0)
        raise AssertionError("expected AutoTypeError")
    except AutoTypeError:
        pass
