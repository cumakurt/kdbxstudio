"""Tests for groups, credentials, and CSV import."""

from pathlib import Path

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.export import export_entries_csv
from kdbxstudio.core.database import InvalidCredentialsError, KdbxDatabase


def test_group_crud(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "g.kdbx", password="secret")
    root = mgr.root_group_uuid()
    group = mgr.add_group(root, "Work")
    assert group.name == "Work"
    renamed = mgr.rename_group(group.uuid, "Office")
    assert renamed.name == "Office"
    mgr.add_entry(group.uuid, title="Laptop")
    mgr.delete_group(group.uuid)
    office = next(g for g in mgr.list_groups() if g.name == "Office")
    assert office.parent_uuid == mgr.recycle_bin_uuid()


def test_ensure_group_path(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "path.kdbx", password="secret")
    leaf = db.ensure_group_path("Root/Work/Dev")
    entry = db.add_entry(leaf, title="CI")
    assert "Work" in entry.group_path
    assert "Dev" in entry.group_path


def test_change_credentials(tmp_path: Path) -> None:
    path = tmp_path / "cred.kdbx"
    db = KdbxDatabase()
    db.create(path, password="old")
    db.change_credentials(password="new")
    db.save()
    db.close()
    db2 = KdbxDatabase()
    try:
        db2.open(path, password="old")
        raise AssertionError("old password should fail")
    except InvalidCredentialsError:
        pass
    db2.open(path, password="new")
    assert db2.is_open


def test_csv_roundtrip_import(tmp_path: Path) -> None:
    src = DatabaseManager()
    src.create(tmp_path / "src.kdbx", password="secret")
    root = src.root_group_uuid()
    work = src.add_group(root, "Work")
    src.add_entry(work.uuid, title="Mail", username="a", password="b", url="https://x")
    csv_path = tmp_path / "data.csv"
    export_entries_csv(csv_path, src.all_entries())

    dst = DatabaseManager()
    dst.create(tmp_path / "dst.kdbx", password="secret")
    result = dst.import_csv(csv_path)
    assert result.created == 1
    titles = {e.title for e in dst.all_entries()}
    assert "Mail" in titles
