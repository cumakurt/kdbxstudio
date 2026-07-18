"""Tests for history, attachments, and plugins."""

from pathlib import Path

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.core.database import KdbxDatabase
from kdbxstudio.plugins.builtin.duplicate_highlight_plugin import create_plugin
from kdbxstudio.plugins.sdk import PluginContext


def test_entry_history(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "hist.kdbx", password="secret")
    root = db.root_group_uuid()
    entry = db.add_entry(root, title="A", password="one")
    db.update_entry(entry.uuid, title="B", password="two")
    history = db.list_history(entry.uuid)
    assert len(history) == 1
    assert history[0].title == "A"
    assert history[0].password == "one"


def test_attachments(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "att.kdbx", password="secret")
    root = mgr.root_group_uuid()
    entry = mgr.add_entry(root, title="Doc")
    att = mgr.add_attachment(entry.uuid, "note.txt", b"hello")
    assert att.filename == "note.txt"
    listed = mgr.list_attachments(entry.uuid)
    assert len(listed) == 1
    assert listed[0].data == b""
    assert listed[0].size == 5
    assert mgr.get_attachment_data(entry.uuid, listed[0].id) == b"hello"
    with_data = mgr.list_attachments(entry.uuid, include_data=True)
    assert with_data[0].data == b"hello"
    mgr.delete_attachment(entry.uuid, att.id)
    assert mgr.list_attachments(entry.uuid) == []


def test_plugin_manager_activate() -> None:
    mgr = PluginManager(PluginContext())
    plugin = create_plugin()
    mgr.register(plugin)
    mgr.activate(plugin.meta.name)
    infos = mgr.list_plugins()
    assert infos[0].active is True
    # Simulate audit hook
    class _Finding:
        kind = "duplicate_password"

    class _Report:
        findings = (_Finding(), _Finding())

    results = mgr.context.emit("audit.completed", report=_Report())
    assert results == [2]
    mgr.deactivate(plugin.meta.name)
    assert mgr.list_plugins()[0].active is False
