"""Recycle Bin listing and empty behavior."""

from __future__ import annotations

from pathlib import Path

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.core.database import KdbxDatabase


def test_list_recycle_bin_includes_direct_trashed_entry(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "direct.kdbx", password="secret")
    entry = db.add_entry(db.root_group_uuid(), title="Direct", password="x")
    db.trash_entry(entry.uuid)
    bin_uuid = db.recycle_bin_uuid()
    assert bin_uuid is not None
    listed = db.list_entries(bin_uuid)
    titles = {e.title for e in listed}
    assert "Direct" in titles
    assert all(e.in_recycle_bin for e in listed)


def test_list_recycle_bin_includes_nested_trashed_group_entries(
    tmp_path: Path,
) -> None:
    """KeePass trashes groups as subgroups — bin must flatten them."""
    db = KdbxDatabase()
    db.create(tmp_path / "nested.kdbx", password="secret")
    group = db.add_group(db.root_group_uuid(), "Work")
    nested = db.add_entry(group.uuid, title="InGroup", password="y")
    direct = db.add_entry(db.root_group_uuid(), title="Direct", password="z")
    db.trash_entry(direct.uuid)
    db.delete_group(group.uuid)

    bin_uuid = db.recycle_bin_uuid()
    assert bin_uuid is not None

    # Non-recursive (old bug): only direct children
    shallow = db.list_entries(bin_uuid, recursive=False)
    assert {e.title for e in shallow} == {"Direct"}

    # Default / recursive: nested secrets appear
    deep = db.list_entries(bin_uuid)
    titles = {e.title for e in deep}
    assert titles == {"Direct", "InGroup"}
    assert all(e.in_recycle_bin for e in deep)
    assert db.get_entry(nested.uuid) is not None


def test_database_manager_list_recycle_bin_recursive(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "mgr.kdbx", password="secret")
    root = mgr.root_group_uuid()
    folder = mgr.add_group(root, "Folder")
    mgr.add_entry(folder.uuid, title="NestedSecret", password="n")
    mgr.add_entry(root, title="TopSecret", password="t")
    top = next(e for e in mgr.all_entries() if e.title == "TopSecret")
    mgr.delete_entries([top.uuid], permanent=False)
    mgr.delete_group(folder.uuid)

    bin_uuid = mgr.recycle_bin_uuid()
    assert bin_uuid is not None
    listed = mgr.list_entries(bin_uuid)
    assert {e.title for e in listed} == {"NestedSecret", "TopSecret"}


def test_empty_recycle_bin_clears_nested(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "empty.kdbx", password="secret")
    group = db.add_group(db.root_group_uuid(), "Folder")
    entry = db.add_entry(group.uuid, title="Nested", password="secret")
    db.delete_group(group.uuid)
    assert len(db.list_entries(db.recycle_bin_uuid())) == 1
    assert db.empty_recycle_bin() == 1
    assert db.get_entry(entry.uuid) is None
    bin_uuid = db.recycle_bin_uuid()
    assert bin_uuid is not None
    assert db.list_entries(bin_uuid) == []


def test_entry_list_shows_recursive_bin_contents(qtbot, tmp_path: Path) -> None:
    """UI widgets display all recycled entries when fed recursive list_entries."""
    from kdbxstudio.ui.widgets.entry_list import EntryListWidget
    from kdbxstudio.ui.widgets.group_tree import GroupTreeWidget

    mgr = DatabaseManager()
    mgr.create(tmp_path / "ui.kdbx", password="secret")
    root = mgr.root_group_uuid()
    folder = mgr.add_group(root, "Work")
    mgr.add_entry(folder.uuid, title="Nested", password="n")
    top = mgr.add_entry(root, title="Top", password="t")
    mgr.delete_entries([top.uuid], permanent=False)
    mgr.delete_group(folder.uuid)
    bin_uuid = mgr.recycle_bin_uuid()
    assert bin_uuid is not None

    tree = GroupTreeWidget()
    entries = EntryListWidget()
    qtbot.addWidget(tree)
    qtbot.addWidget(entries)

    groups = mgr.list_groups()
    tree.set_groups(groups, root, select_uuid=bin_uuid)
    assert tree.selected_group_uuid() == bin_uuid

    listed = mgr.list_entries(bin_uuid)  # recursive by default for bin
    entries.set_entries(listed)
    titles = [
        entries._model.entry_at(r).title  # noqa: SLF001
        for r in range(entries._model.rowCount())  # noqa: SLF001
    ]
    assert set(titles) == {"Nested", "Top"}
