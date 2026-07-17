"""Tests for recycle bin and multi-session manager."""

from pathlib import Path

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.core.database import KdbxDatabase
from kdbxstudio.security.settings import SecuritySettings


def test_trash_and_empty_recycle_bin(tmp_path: Path) -> None:
    path = tmp_path / "bin.kdbx"
    db = KdbxDatabase()
    db.create(path, password="secret")
    root = db.root_group_uuid()
    entry = db.add_entry(root, title="Temp", password="abc12345")
    db.trash_entry(entry.uuid)
    recycled = db.get_entry(entry.uuid)
    assert recycled is not None
    assert recycled.in_recycle_bin is True
    assert db.recycle_bin_uuid() is not None
    removed = db.empty_recycle_bin()
    assert removed == 1
    assert db.get_entry(entry.uuid) is None


def test_multi_session_tabs(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    a = mgr.create(tmp_path / "a.kdbx", password="a")
    b = mgr.create(tmp_path / "b.kdbx", password="b")
    assert set(mgr.session_ids()) == {a, b}
    assert mgr.active_id == b
    mgr.set_active(a)
    assert mgr.active_id == a
    assert mgr.any_dirty() is False
    root = mgr.root_group_uuid()
    mgr.add_entry(root, title="X")
    assert mgr.any_dirty() is True


def test_security_settings_replace() -> None:
    s = SecuritySettings()
    updated = s.with_updates(clipboard_timeout_ms=30_000, auto_lock_enabled=False)
    assert updated.clipboard_timeout_ms == 30_000
    assert updated.auto_lock_enabled is False
    assert s.clipboard_timeout_ms == 15_000
