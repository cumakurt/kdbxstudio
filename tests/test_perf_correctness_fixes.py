"""Regression tests for 2026-07-18 perf/correctness fixes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QLineEdit

from kdbxstudio.application.audit_engine import AuditEngine
from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.expiry import EXPIRING_SOON_DAYS, is_expiring_soon
from kdbxstudio.application.hibp import (
    HibpError,
    fetch_range,
    reset_hibp_cache_for_tests,
)
from kdbxstudio.application.merge import merge_databases
from kdbxstudio.application.search_engine import EntryFilter, SearchEngine
from kdbxstudio.application.security_dashboard import SecurityDashboardAnalyzer
from kdbxstudio.core.database import EntryView, KdbxDatabase
from kdbxstudio.ui.widgets.entry_detail import EntryDetailWidget
from kdbxstudio.ui.widgets.filter_bar import FilterBarWidget
from kdbxstudio.ui.widgets.group_tree import GroupTreeWidget


def test_all_entries_returns_list_copy(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "copy.kdbx", password="secret")
    mgr.add_entry(mgr.root_group_uuid(), title="A", password="x")
    first = mgr.all_entries()
    first.clear()
    second = mgr.all_entries()
    assert len(second) == 1
    assert second[0].title == "A"


def test_entry_view_attachment_count_and_lazy_data(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "att.kdbx", password="secret")
    entry = db.add_entry(db.root_group_uuid(), title="Doc")
    db.add_attachment(entry.uuid, "a.bin", b"payload-bytes")
    views = db.list_entries()
    assert views[0].attachment_count == 1
    meta = db.list_attachments(entry.uuid)
    assert meta[0].data == b""
    assert meta[0].size == len(b"payload-bytes")
    assert db.get_attachment_data(entry.uuid, meta[0].id) == b"payload-bytes"


def test_audit_uses_attachment_count_without_n_plus_one(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "audit.kdbx", password="secret")
    root = mgr.root_group_uuid()
    for i in range(5):
        entry = mgr.add_entry(root, title=f"E{i}", password=f"StrongPass!{i}Xx")
        if i % 2 == 0:
            mgr.add_attachment(entry.uuid, f"{i}.bin", b"x")
    engine = AuditEngine(mgr)
    with patch.object(
        mgr, "attachment_count", side_effect=AssertionError("N+1 attachment_count")
    ):
        report = engine.run()
    assert report.entries_with_attachments == 3


def test_audit_list_groups_respects_session_id(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    sid_a = mgr.create(tmp_path / "a.kdbx", password="a")
    sid_b = mgr.create(tmp_path / "b.kdbx", password="b")
    mgr.add_group(mgr.root_group_uuid(sid_b), "Extra", session_id=sid_b)
    engine = AuditEngine(mgr)
    report_a = engine.run(session_id=sid_a)
    report_b = engine.run(session_id=sid_b)
    assert report_b.total_groups > report_a.total_groups


def test_merge_attachments_add_before_delete(tmp_path: Path) -> None:
    src = KdbxDatabase()
    dst = KdbxDatabase()
    src.create(tmp_path / "s.kdbx", password="a")
    dst.create(tmp_path / "d.kdbx", password="b")
    source_entry = src.add_entry(src.root_group_uuid(), title="Shared", password="1")
    src.add_attachment(source_entry.uuid, "new.txt", b"new-payload")
    dest_entry = dst.add_entry(dst.root_group_uuid(), title="Shared", password="0")
    dst.add_attachment(dest_entry.uuid, "old.txt", b"old-payload")
    merge_databases(dst, src, update_existing=True)
    merged = next(e for e in dst.list_entries() if e.title == "Shared")
    attachments = dst.list_attachments(merged.uuid, include_data=True)
    assert len(attachments) == 1
    assert attachments[0].filename == "new.txt"
    assert attachments[0].data == b"new-payload"


def test_expiring_soon_constant_shared() -> None:
    assert EXPIRING_SOON_DAYS == AuditEngine.EXPIRING_SOON_DAYS
    now = datetime.now(UTC)
    entry = EntryView(
        uuid="1",
        title="t",
        username="",
        password="x",
        url="",
        notes="",
        group_path="Root",
        expires=True,
        expiry_time=(now + timedelta(days=EXPIRING_SOON_DAYS - 1)).isoformat(),
    )
    assert is_expiring_soon(entry, now=now) is True
    far = EntryView(
        uuid="2",
        title="t",
        username="",
        password="x",
        url="",
        notes="",
        group_path="Root",
        expires=True,
        expiry_time=(now + timedelta(days=EXPIRING_SOON_DAYS + 5)).isoformat(),
    )
    assert is_expiring_soon(far, now=now) is False


def test_search_expiring_soon_uses_shared_window(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "exp.kdbx", password="secret")
    now = datetime.now(UTC)
    soon = now + timedelta(days=max(1, EXPIRING_SOON_DAYS - 2))
    later = now + timedelta(days=EXPIRING_SOON_DAYS + 10)
    mgr.add_entry(
        mgr.root_group_uuid(),
        title="Soon",
        password="StrongPass!Aa1",
        expires=True,
        expiry_time=soon,
    )
    mgr.add_entry(
        mgr.root_group_uuid(),
        title="Later",
        password="StrongPass!Bb2",
        expires=True,
        expiry_time=later,
    )
    search = SearchEngine(mgr)
    hits = search.search("", entry_filter=EntryFilter(expiring_soon_only=True))
    titles = {h.entry.title for h in hits}
    assert titles == {"Soon"}


def test_hibp_memory_cache_avoids_repeated_disk_load(
    tmp_path: Path, monkeypatch
) -> None:
    reset_hibp_cache_for_tests()
    cache_file = tmp_path / "prefix_cache.json"
    monkeypatch.setattr("kdbxstudio.application.hibp._cache_path", lambda: cache_file)
    body = "AABBCCDD11223344556677889900AABB:3\n"

    class _Resp:
        def read(self, _size: int = -1) -> bytes:
            return body.encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch("urllib.request.urlopen", return_value=_Resp()) as mocked:
        first = fetch_range("ABCDE")
        second = fetch_range("ABCDE")
    assert first == second
    assert mocked.call_count == 1


def test_hibp_rejects_oversized_response(tmp_path: Path, monkeypatch) -> None:
    reset_hibp_cache_for_tests()
    monkeypatch.setattr(
        "kdbxstudio.application.hibp._cache_path", lambda: tmp_path / "cache.json"
    )

    class _Resp:
        def read(self, size: int = -1) -> bytes:
            return b"X" * size

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    with patch("urllib.request.urlopen", return_value=_Resp()):
        with pytest.raises(HibpError, match="safety limit"):
            fetch_range("ABCDE")


def test_password_show_resets_on_load_entry(qtbot) -> None:
    widget = EntryDetailWidget()
    qtbot.addWidget(widget)
    entry_a = EntryView(
        uuid="a",
        title="A",
        username="u",
        password="secret-a",
        url="",
        notes="",
        group_path="Root",
    )
    entry_b = EntryView(
        uuid="b",
        title="B",
        username="u",
        password="secret-b",
        url="",
        notes="",
        group_path="Root",
    )
    widget.load_entry(entry_a)
    widget._show_btn.setChecked(True)
    assert widget._password.echoMode() == QLineEdit.EchoMode.Normal
    widget.load_entry(entry_b)
    assert widget._show_btn.isChecked() is False
    assert widget._password.echoMode() == QLineEdit.EchoMode.Password


def test_group_tree_select_uuid(qtbot, tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "groups.kdbx", password="secret")
    root = mgr.root_group_uuid()
    child = mgr.add_group(root, "Child")
    tree = GroupTreeWidget()
    qtbot.addWidget(tree)
    tree.set_groups(mgr.list_groups(), root, select_uuid=child.uuid)
    assert tree.selected_group_uuid() == child.uuid
    root_item_selected = tree.select_uuid(root)
    assert root_item_selected is True
    assert tree.selected_group_uuid() == root
    assert tree.select_uuid("missing-uuid") is False


def test_filter_bar_clear_emits_once(qtbot) -> None:
    bar = FilterBarWidget()
    qtbot.addWidget(bar)
    emissions: list[object] = []
    bar.filter_changed.connect(emissions.append)
    bar._weak.setChecked(True)
    bar._empty.setChecked(True)
    emissions.clear()
    bar.clear()
    assert len(emissions) == 1
    assert emissions[0].is_empty()


def test_filter_bar_reflows_at_compact_width(qtbot) -> None:
    bar = FilterBarWidget()
    qtbot.addWidget(bar)
    bar.resize(620, 180)
    bar.show()
    qtbot.wait(10)
    assert bar._layout_mode == "compact"
    assert bar._layout.rowCount() >= 4
    assert all(chip.isVisible() for chip in bar._chips)


def test_dashboard_attachment_stats_use_requested_session(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    session_a = mgr.create(tmp_path / "a.kdbx", password="a")
    entry_a = mgr.add_entry(mgr.root_group_uuid(), title="A")
    mgr.add_attachment(entry_a.uuid, "a.txt", b"a")
    session_b = mgr.create(tmp_path / "b.kdbx", password="b")
    entry_b = mgr.add_entry(mgr.root_group_uuid(), title="B")
    mgr.add_attachment(entry_b.uuid, "b.txt", b"b")
    mgr.add_attachment(entry_b.uuid, "c.txt", b"c")
    assert mgr.active_id == session_b

    snapshot = SecurityDashboardAnalyzer(mgr).run(session_a)
    assert snapshot.attachment_total == 1
