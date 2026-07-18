"""Expiry date editor behaviour in EntryDetailWidget."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from PySide6.QtCore import QDate

from kdbxstudio.application.expiry import (
    expiry_local_date_iso,
    local_date_to_utc_end_of_day,
)
from kdbxstudio.core.database import EntryView
from kdbxstudio.ui.widgets.entry_detail import EntryDetailWidget


def test_expiry_date_editable_when_expires_loaded(qtbot) -> None:
    widget = EntryDetailWidget()
    qtbot.addWidget(widget)
    when = datetime.now(UTC) + timedelta(days=12)
    entry = EntryView(
        uuid="e1",
        title="Card",
        username="u",
        password="p",
        url="",
        notes="",
        group_path="Root",
        expires=True,
        expiry_time=when.isoformat(),
    )
    widget.load_entry(entry)
    assert widget._has_expiry.isChecked() is True
    assert widget._expiry_date.isEnabled() is True
    assert widget._expiry_date.isReadOnly() is False
    line = widget._expiry_date.lineEdit()
    assert line is not None and line.isReadOnly() is False

    target = QDate.currentDate().addDays(40)
    widget._expiry_date.setDate(target)
    assert widget._expiry_date.date() == target

    saved: list[dict] = []
    widget.save_requested.connect(saved.append)
    widget._emit_save()
    assert saved
    assert saved[0]["expires"] is True
    assert saved[0]["expiry_time"] == target.toString("yyyy-MM-dd")


def test_expiry_local_date_roundtrip() -> None:
    local_day = datetime.now().astimezone().date() + timedelta(days=3)
    utc = local_date_to_utc_end_of_day(local_day.isoformat())
    entry = EntryView(
        uuid="e2",
        title="t",
        username="",
        password="",
        url="",
        notes="",
        group_path="Root",
        expires=True,
        expiry_time=utc.isoformat(),
    )
    assert expiry_local_date_iso(entry) == local_day.isoformat()


def test_choosing_expires_on_enables_date(qtbot) -> None:
    widget = EntryDetailWidget()
    qtbot.addWidget(widget)
    entry = EntryView(
        uuid="e3",
        title="t",
        username="",
        password="",
        url="",
        notes="",
        group_path="Root",
        expires=False,
    )
    widget.load_entry(entry)
    assert widget._expiry_date.isEnabled() is False
    widget._has_expiry.setChecked(True)
    assert widget._expiry_date.isEnabled() is True
    assert widget._expiry_date.isReadOnly() is False
