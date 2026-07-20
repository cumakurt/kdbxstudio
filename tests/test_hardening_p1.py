"""Tests for post-audit hardening: secrets redact, plugins, perms, jobs."""

from __future__ import annotations

import stat
from pathlib import Path

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.core.database import redact_entry_secrets
from kdbxstudio.core.paths import ensure_private_dir
from kdbxstudio.plugins.sdk import PluginContext
from kdbxstudio.security.audit_log import audit_log_path, log_security_event


def test_list_entries_can_omit_secrets(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "sec.kdbx", password="master")
    root = mgr.root_group_uuid()
    entry = mgr.add_entry(root, title="A", password="secret", notes="n")
    mgr.update_entry(entry.uuid, otp="otpauth://totp/x?secret=JBSWY3DPEHPK3PXP")
    redacted = mgr.list_entries(include_secrets=False)
    assert redacted
    assert redacted[0].password == ""
    assert redacted[0].otp == ""
    full = mgr.get_entry(entry.uuid)
    assert full is not None
    assert full.password == "secret"
    assert full.otp


def test_all_entries_redact_flag(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "all.kdbx", password="master")
    mgr.add_entry(mgr.root_group_uuid(), title="B", password="p")
    meta = mgr.all_entries(include_secrets=False)
    assert meta[0].password == ""
    secrets = mgr.all_entries(include_secrets=True)
    assert secrets[0].password == "p"


def test_redact_entry_helper() -> None:
    from kdbxstudio.core.database import EntryView

    entry = EntryView(
        uuid="u",
        title="t",
        username="u",
        password="x",
        url="",
        notes="",
        group_path="Root",
        otp="otp",
    )
    out = redact_entry_secrets(entry)
    assert out.password == ""
    assert out.otp == ""
    assert out.title == "t"


def test_attachment_stats_batch(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "att.kdbx", password="master")
    root = mgr.root_group_uuid()
    e1 = mgr.add_entry(root, title="One")
    e2 = mgr.add_entry(root, title="Two")
    mgr.add_attachment(e1.uuid, "a.txt", b"hello")
    mgr.add_attachment(e2.uuid, "b.bin", b"12345")
    stats = mgr.attachment_stats()
    assert len(stats) == 2
    sizes = sorted(s for _u, _n, s in stats)
    assert sizes == [5, 5]


def test_ensure_private_dir_mode(tmp_path: Path) -> None:
    target = ensure_private_dir(tmp_path / "private")
    mode = stat.S_IMODE(target.stat().st_mode)
    assert mode == 0o700


def test_plugin_discover_fail_closed(tmp_path: Path) -> None:
    plugin_path = tmp_path / "x_plugin.py"
    plugin_path.write_text(
        "from kdbxstudio.plugins.sdk import Plugin, PluginMeta\n"
        "class _P(Plugin):\n"
        "    meta = PluginMeta(name='x', version='1', description='d')\n"
        "    def activate(self, context): pass\n"
        "    def deactivate(self, context): pass\n"
        "def create_plugin():\n"
        "    return _P()\n",
        encoding="utf-8",
    )
    mgr = PluginManager(PluginContext())
    assert mgr.discover(tmp_path) == []
    assert mgr.discover(tmp_path, allow_unverified=True) == ["x"]


def test_security_audit_log_writes(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    log_security_event("test_event", database="demo.kdbx")
    path = audit_log_path()
    assert path.is_file()
    assert "test_event" in path.read_text(encoding="utf-8")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
