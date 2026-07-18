"""Tests for TOTP, history restore, CSV export."""

from pathlib import Path

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.export import export_entries_csv
from kdbxstudio.core.totp import current_totp


def test_totp_from_uri() -> None:
    uri = (
        "otpauth://totp/Example:user?secret=JBSWY3DPEHPK3PXP&issuer=Example&period=30"
    )
    status = current_totp(uri)
    assert status.valid is True
    assert len(status.code) == 6
    assert 1 <= status.remaining_seconds <= 30


def test_history_restore(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "hist.kdbx", password="secret")
    root = mgr.root_group_uuid()
    entry = mgr.add_entry(root, title="One", password="old")
    mgr.update_entry(entry.uuid, title="Two", password="new")
    history = mgr.list_history(entry.uuid)
    assert len(history) == 1
    assert history[0].title == "One"
    restored = mgr.restore_history(entry.uuid, 0)
    assert restored.title == "One"
    assert restored.password == "old"
    # current "Two" should now be in history
    assert any(h.title == "Two" for h in mgr.list_history(entry.uuid))


def test_csv_export(tmp_path: Path) -> None:
    import stat

    mgr = DatabaseManager()
    mgr.create(tmp_path / "exp.kdbx", password="secret")
    root = mgr.root_group_uuid()
    mgr.add_entry(root, title="Mail", username="a", password="b", url="https://x")
    out = tmp_path / "out.csv"
    export_entries_csv(out, mgr.all_entries())
    text = out.read_text(encoding="utf-8")
    assert "Mail" in text
    assert "password" in text.splitlines()[0]
    assert stat.S_IMODE(out.stat().st_mode) == 0o600


def test_emergency_sheet_write_is_user_rw_only(tmp_path: Path) -> None:
    import stat

    from kdbxstudio.application.emergency_sheet import write_emergency_html
    from kdbxstudio.core.database import EntryView

    entry = EntryView(
        uuid="u1",
        title="Bank",
        username="u",
        password="secret",
        url="",
        notes="",
        group_path="Root",
    )
    out = write_emergency_html(tmp_path / "sheet.html", [entry])
    assert "Bank" in out.read_text(encoding="utf-8")
    assert stat.S_IMODE(out.stat().st_mode) == 0o600


def test_database_info(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "info.kdbx", password="secret")
    info = mgr.database_info()
    assert info.entry_count == 0
    assert info.group_count >= 1
    assert info.dirty is False
    assert "info.kdbx" in info.path
