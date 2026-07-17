"""Tests for KdbxDatabase and DatabaseManager."""

from pathlib import Path

import pytest

from kdbxstudio.application.audit_engine import AuditEngine
from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.search_engine import SearchEngine
from kdbxstudio.core.database import InvalidCredentialsError, KdbxDatabase


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.kdbx"


def test_create_open_save_roundtrip(db_path: Path) -> None:
    db = KdbxDatabase()
    db.create(db_path, password="secret")
    root = db.root_group_uuid()
    entry = db.add_entry(root, title="GitHub", username="me", password="p@ss")
    db.save()
    db.close()

    db2 = KdbxDatabase()
    db2.open(db_path, password="secret")
    loaded = db2.get_entry(entry.uuid)
    assert loaded is not None
    assert loaded.title == "GitHub"
    assert loaded.username == "me"
    assert loaded.password == "p@ss"


def test_invalid_credentials(db_path: Path) -> None:
    db = KdbxDatabase()
    db.create(db_path, password="correct")
    db.close()

    db2 = KdbxDatabase()
    with pytest.raises(InvalidCredentialsError):
        db2.open(db_path, password="wrong")


def test_database_manager_and_search(db_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(db_path, password="secret")
    root = mgr.root_group_uuid()
    mgr.add_entry(root, title="Alpha", username="a", url="https://a.example")
    mgr.add_entry(root, title="Beta", username="b", notes="secret note")
    mgr.save()

    search = SearchEngine(mgr)
    hits = search.search("alpha")
    assert len(hits) == 1
    assert hits[0].entry.title == "Alpha"

    note_hits = search.search("secret note")
    assert len(note_hits) == 1
    assert note_hits[0].entry.title == "Beta"


def test_audit_engine(db_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(db_path, password="secret")
    root = mgr.root_group_uuid()
    mgr.add_entry(root, title="Empty", password="")
    mgr.add_entry(root, title="Weak", password="123")
    mgr.add_entry(root, title="Dup1", password="samepass123")
    mgr.add_entry(root, title="Dup2", password="samepass123")

    report = AuditEngine(mgr).run()
    assert report.total_entries == 4
    assert report.empty_passwords == 1
    assert report.weak_passwords == 1
    assert report.duplicates == 2
    kinds = {f.kind for f in report.findings}
    assert "empty_password" in kinds
    assert "weak_password" in kinds
    assert "duplicate_password" in kinds
