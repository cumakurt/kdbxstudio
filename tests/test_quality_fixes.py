"""Regression tests for code-quality fixes."""

from __future__ import annotations

import json
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from kdbxstudio.application.autotype import AutoTypeError, auto_type, expand_sequence
from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.expiry import is_expired, local_date_to_utc_end_of_day
from kdbxstudio.application.export import export_entries_csv
from kdbxstudio.application.import_csv import import_entries_csv
from kdbxstudio.application.merge import merge_databases
from kdbxstudio.application.plugin_manager import PluginError, PluginManager
from kdbxstudio.application.search_engine import EntryFilter, SearchEngine
from kdbxstudio.browser import install_host
from kdbxstudio.core.database import DatabaseError, EntryView, KdbxDatabase
from kdbxstudio.core.paths import resolve_regular_file
from kdbxstudio.plugins.sdk import PluginContext, PluginMeta
from kdbxstudio.security.settings import SecuritySettings
from kdbxstudio.security.store import load_settings, save_settings


def test_native_host_install_writes_private_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setattr(install_host.shutil, "which", lambda _name: None)

    manifests = install_host.install()
    launcher = tmp_path / "data" / "kdbxstudio" / "keepassxc-proxy.sh"
    assert stat.S_IMODE(launcher.stat().st_mode) == 0o700
    assert manifests
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in manifests)


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


def test_csv_expiry_preserves_timezone(tmp_path: Path) -> None:
    db_path = tmp_path / "exp.kdbx"
    csv_path = tmp_path / "exp.csv"
    csv_path.write_text(
        "title,username,password,url,notes,group,expires,expiry_time\n"
        "Dated,u,p,,,Root,true,2030-06-15T22:30:00+03:00\n",
        encoding="utf-8",
    )
    db = KdbxDatabase()
    db.create(db_path, password="pass")
    import_entries_csv(db, csv_path)
    entry = next(e for e in db.list_entries() if e.title == "Dated")
    assert entry.expires
    # +03:00 22:30 == 19:30 UTC (pykeepass may normalize)
    assert "19:30" in entry.expiry_time or "+03:00" in entry.expiry_time


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
        favicon_downloads_enabled=True,
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


def test_plugin_deactivate_failure_clears_hooks() -> None:
    class Broken:
        meta = PluginMeta(name="broken", version="1")

        def activate(self, context: PluginContext) -> None:
            context.register_hook("ping", lambda **_: 1, owner=self.meta.name)

        def deactivate(self, context: PluginContext) -> None:
            raise RuntimeError("boom")

    mgr = PluginManager()
    mgr.register(Broken())
    mgr.activate("broken")
    assert mgr.context.emit("ping") == [1]
    try:
        mgr.deactivate("broken")
        raise AssertionError("expected PluginError")
    except PluginError:
        pass
    assert mgr.context.emit("ping") == []
    assert mgr.list_plugins()[0].active is False


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


def test_merge_copies_expiry(tmp_path: Path) -> None:
    src = KdbxDatabase()
    dst = KdbxDatabase()
    src.create(tmp_path / "s.kdbx", password="a")
    dst.create(tmp_path / "d.kdbx", password="b")
    expiry = datetime(2031, 3, 1, 12, 0, tzinfo=UTC)
    created = src.add_entry(src.root_group_uuid(), title="Dated", password="x")
    src.update_entry(created.uuid, expires=True, expiry_time=expiry)
    merge_databases(dst, src)
    entry = next(e for e in dst.list_entries() if e.title == "Dated")
    assert entry.expires
    assert "2031-03-01" in entry.expiry_time


def test_resolve_regular_file_rejects_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.txt"
    real.write_text("secret", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(real)
    assert resolve_regular_file(real) == real.resolve()
    assert resolve_regular_file(link) is None
    assert resolve_regular_file(tmp_path / "missing.txt") is None


def test_empty_recycle_bin_purges_trashed_groups(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "bin.kdbx", password="x")
    group = db.add_group(db.root_group_uuid(), "Work")
    entry = db.add_entry(group.uuid, title="Secret", password="pw")
    db.delete_group(group.uuid)
    assert db.get_entry(entry.uuid) is not None
    assert db.get_entry(entry.uuid).in_recycle_bin  # type: ignore[union-attr]
    removed = db.empty_recycle_bin()
    assert removed == 1
    assert db.get_entry(entry.uuid) is None
    assert db.database_info().recycle_bin_entries == 0


def test_restore_history_restores_tags_and_expiry(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "hist.kdbx", password="x")
    root = db.root_group_uuid()
    expiry = datetime(2032, 1, 15, 12, 0, tzinfo=UTC)
    entry = db.add_entry(
        root,
        title="Old",
        password="1",
        tags=["alpha"],
        expires=True,
        expiry_time=expiry,
    )
    db.update_entry(entry.uuid, custom_properties={"env": "prod"})
    db.update_entry(
        entry.uuid,
        title="New",
        password="2",
        tags=["beta"],
        expires=False,
        custom_properties={},
    )
    restored = db.restore_history(entry.uuid, 0)
    assert restored.title == "Old"
    assert restored.tags == ("alpha",)
    assert restored.expires is True
    assert "2032-01-15" in restored.expiry_time
    assert restored.custom_properties.get("env") == "prod"


def test_merge_copies_attachments_and_clears_otp(tmp_path: Path) -> None:
    src = KdbxDatabase()
    dst = KdbxDatabase()
    src.create(tmp_path / "s.kdbx", password="a")
    dst.create(tmp_path / "d.kdbx", password="b")
    source_entry = src.add_entry(src.root_group_uuid(), title="Shared", password="1")
    src.add_attachment(source_entry.uuid, "note.txt", b"payload")
    dest_entry = dst.add_entry(dst.root_group_uuid(), title="Shared", password="0")
    dst.update_entry(dest_entry.uuid, otp="otpauth://totp/old?secret=JBSWY3DPEHPK3PXP")
    merge_databases(dst, src, update_existing=True)
    merged = next(e for e in dst.list_entries() if e.title == "Shared")
    assert merged.otp == ""
    attachments = dst.list_attachments(merged.uuid, include_data=True)
    assert len(attachments) == 1
    assert attachments[0].filename == "note.txt"
    assert attachments[0].data == b"payload"


def test_add_attachment_rejects_path_traversal_name(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "att.kdbx", password="x")
    entry = db.add_entry(db.root_group_uuid(), title="A")
    view = db.add_attachment(entry.uuid, "../evil.txt", b"x")
    assert view.filename == "evil.txt"
    assert ".." not in view.filename


def test_autotype_expand_still_works() -> None:
    assert expand_sequence("{TAB}", username="", password="") == [("key", "Tab")]
    huge = expand_sequence("{DELAY=999999999999999}", username="", password="")
    assert huge == [("delay", "60000")]


def test_autotype_missing_backend_raises(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import kdbxstudio.application.autotype as mod

    monkeypatch.setattr(mod, "detect_backend", lambda: None)
    try:
        auto_type("{PASSWORD}", username="", password="x", initial_delay_ms=0)
        raise AssertionError("expected AutoTypeError")
    except AutoTypeError:
        pass


@pytest.mark.parametrize(
    ("function_name", "expected_command"),
    [
        (
            "_type_xdotool",
            ["xdotool", "type", "--clearmodifiers", "--delay", "12", "--file", "-"],
        ),
        ("_type_ydotool", ["ydotool", "stdin"]),
        ("_type_wtype", ["wtype", "-"]),
    ],
)
def test_autotype_secrets_are_passed_via_stdin(
    function_name: str, expected_command: list[str]
) -> None:
    import kdbxstudio.application.autotype as mod

    secret = "not-visible-in-process-list"
    with patch.object(mod.subprocess, "run") as run:
        getattr(mod, function_name)(secret)
    assert run.call_args.args[0] == expected_command
    assert secret not in run.call_args.args[0]
    assert run.call_args.kwargs["input"] == secret


def test_database_create_and_save_are_owner_only(tmp_path: Path) -> None:
    path = tmp_path / "private.kdbx"
    db = KdbxDatabase()
    db.create(path, password="secret")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    db.add_entry(db.root_group_uuid(), title="A", password="p")
    db.save()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_failed_database_save_keeps_original_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "atomic.kdbx"
    db = KdbxDatabase()
    db.create(path, password="secret")
    original = path.read_bytes()
    db.add_entry(db.root_group_uuid(), title="Unsaved", password="p")

    def fail_after_partial_write(handle) -> None:  # type: ignore[no-untyped-def]
        handle.write(b"partial")
        raise OSError("simulated write failure")

    monkeypatch.setattr(db._require_kp(), "save", fail_after_partial_write)  # noqa: SLF001
    with pytest.raises(DatabaseError):
        db.save()
    assert path.read_bytes() == original
    assert db.is_dirty is True


def test_plaintext_export_replaces_symlink_without_touching_target(
    tmp_path: Path,
) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("keep", encoding="utf-8")
    destination = tmp_path / "export.csv"
    destination.symlink_to(victim)
    entry = EntryView(
        uuid="1",
        title="Login",
        username="user",
        password="secret",
        url="https://example.com",
        notes="",
        group_path="Root",
    )
    export_entries_csv(destination, [entry])
    assert victim.read_text(encoding="utf-8") == "keep"
    assert destination.is_symlink() is False
    assert "secret" in destination.read_text(encoding="utf-8")
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600


def test_malformed_settings_use_safe_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "auto_lock_enabled": "false",
                "hibp_enabled": "not-a-bool",
                "favicon_downloads_enabled": "not-a-bool",
                "autotype_initial_delay_ms": "not-a-number",
                "auto_lock_timeout_ms": 10**30,
            }
        ),
        encoding="utf-8",
    )
    loaded = load_settings(path)
    assert loaded.auto_lock_enabled is False
    assert loaded.hibp_enabled is SecuritySettings.hibp_enabled
    assert (
        loaded.favicon_downloads_enabled is SecuritySettings.favicon_downloads_enabled
    )
    assert (
        loaded.autotype_initial_delay_ms == SecuritySettings.autotype_initial_delay_ms
    )
    assert loaded.auto_lock_timeout_ms <= 2_147_000_000


def test_failed_reopen_preserves_existing_session(tmp_path: Path) -> None:
    path = tmp_path / "reload.kdbx"
    mgr = DatabaseManager()
    session_id = mgr.create(path, password="secret")
    entry = mgr.add_entry(mgr.root_group_uuid(), title="In memory", password="p")
    path.write_bytes(b"corrupt external replacement")
    with pytest.raises(DatabaseError):
        mgr.open(path, password="secret")
    assert mgr.active_id == session_id
    assert mgr.get_entry(entry.uuid) is not None
