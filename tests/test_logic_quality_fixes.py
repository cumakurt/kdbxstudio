"""Regression tests for 2026-07-18 quality / logic fixes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from kdbxstudio.application.history_diff import diff_history
from kdbxstudio.core.database import HistoryView, KdbxDatabase
from kdbxstudio.core.password_generator import PRESETS
from kdbxstudio.security.settings import SecuritySettings
from kdbxstudio.security.store import load_settings, save_settings
from kdbxstudio.ui.widgets.entry_detail import _estimate_password_strength


def test_password_strength_rewards_long_passwords() -> None:
    short12, _ = _estimate_password_strength("Abcdef12!xyz")
    long16, label = _estimate_password_strength("Abcdef12!xyzABCD")
    assert long16 > short12
    assert label in {"Fair", "Good", "Strong"}


def test_history_diff_includes_tags_for_history_views() -> None:
    before = HistoryView(
        index=0,
        title="A",
        username="u",
        password="p",
        url="",
        notes="",
        modified="",
        tags=("old",),
        custom_properties={"k": "1"},
        expires=True,
        expiry_time="2030-01-01T00:00:00+00:00",
    )
    after = HistoryView(
        index=1,
        title="A",
        username="u",
        password="p",
        url="",
        notes="",
        modified="",
        tags=("new",),
        custom_properties={"k": "2"},
        expires=False,
        expiry_time="",
    )
    fields = {d.field for d in diff_history(before, after)}
    assert fields >= {"tags", "custom", "expiry"}


def test_list_history_exposes_tags_and_expiry(tmp_path: Path) -> None:
    db = KdbxDatabase()
    db.create(tmp_path / "h.kdbx", password="x")
    root = db.root_group_uuid()
    expiry = datetime.now(UTC) + timedelta(days=30)
    entry = db.add_entry(
        root,
        title="T",
        password="1",
        tags=["alpha"],
        expires=True,
        expiry_time=expiry,
    )
    db.update_entry(entry.uuid, custom_properties={"Env": "prod"})
    db.update_entry(entry.uuid, title="T2", tags=["beta"], expires=False)
    history = db.list_history(entry.uuid)
    assert history
    newest = history[0]
    assert "alpha" in newest.tags or newest.custom_properties.get("Env") == "prod"


def test_clipboard_timeout_zero_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    save_settings(SecuritySettings(clipboard_timeout_ms=0), path=path)
    loaded = load_settings(path=path)
    assert loaded.clipboard_timeout_ms == 0


def test_generator_presets_include_long_alphanumeric() -> None:
    names = {p.name for p in PRESETS}
    assert "Long alphanumeric" in names
    assert "Passphrase-like" not in names
