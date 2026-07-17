"""Tests for new application helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from kdbxstudio.application.autotype import expand_sequence
from kdbxstudio.application.emergency_sheet import render_emergency_html
from kdbxstudio.application.favicon import normalize_host
from kdbxstudio.application.hibp import password_sha1
from kdbxstudio.application.history_diff import diff_history
from kdbxstudio.application.merge import merge_databases
from kdbxstudio.core.database import EntryView, HistoryView, KdbxDatabase


def test_expand_autotype_sequence() -> None:
    steps = expand_sequence(
        "{USERNAME}{TAB}{PASSWORD}{ENTER}",
        username="ada",
        password="secret",
    )
    assert steps == [
        ("type", "ada"),
        ("key", "Tab"),
        ("type", "secret"),
        ("key", "Return"),
    ]


def test_password_sha1_known() -> None:
    # SHA1("password")
    assert password_sha1("password") == "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8"


def test_normalize_host() -> None:
    assert normalize_host("https://Example.COM/path") == "example.com"
    assert normalize_host("") is None


def test_history_diff_masks_password() -> None:
    before = HistoryView(
        index=0,
        title="a",
        username="u",
        password="old",
        url="",
        notes="",
        modified="",
    )
    after = HistoryView(
        index=1,
        title="a",
        username="u",
        password="new",
        url="",
        notes="",
        modified="",
    )
    diffs = diff_history(before, after, mask_secrets=True)
    assert len(diffs) == 1
    assert diffs[0].field == "password"
    assert diffs[0].before == "••••••••"


def test_emergency_html_contains_title() -> None:
    entry = EntryView(
        uuid="1",
        title="Vault",
        username="u",
        password="p",
        url="",
        notes="",
        group_path="Root",
        tags=("work",),
    )
    html = render_emergency_html([entry], include_passwords=False)
    assert "Vault" in html
    assert "••••••••" in html


def test_merge_adds_missing_entries(tmp_path: Path) -> None:
    src_path = tmp_path / "src.kdbx"
    dst_path = tmp_path / "dst.kdbx"
    src = KdbxDatabase()
    src.create(src_path, password="src-pass")
    root = src.root_group_uuid()
    src.add_entry(root, title="OnlyInSrc", username="a", password="b")
    src.save()

    dst = KdbxDatabase()
    dst.create(dst_path, password="dst-pass")
    result = merge_databases(dst, src)
    assert result.added == 1
    titles = {e.title for e in dst.list_entries()}
    assert "OnlyInSrc" in titles


def test_entry_tags_and_expiry_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "tags.kdbx"
    db = KdbxDatabase()
    db.create(path, password="pass")
    root = db.root_group_uuid()
    entry = db.add_entry(root, title="Tagged", tags=["alpha", "beta"])
    when = datetime.now(UTC) + timedelta(days=30)
    db.update_entry(
        entry.uuid,
        expires=True,
        expiry_time=when,
        tags=["alpha", "gamma"],
    )
    loaded = db.get_entry(entry.uuid)
    assert loaded is not None
    assert loaded.tags == ("alpha", "gamma")
    assert loaded.expires is True
    assert loaded.expiry_time
