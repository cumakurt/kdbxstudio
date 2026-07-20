"""Export helpers."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from kdbxstudio.core.database import EntryView
from kdbxstudio.core.paths import atomic_write_private


def export_entries_csv(path: Path | str, entries: list[EntryView]) -> Path:
    """Write entries to a CSV file (passwords included — handle carefully)."""
    target = Path(path)
    handle = io.StringIO(newline="")
    try:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "title",
                "username",
                "password",
                "url",
                "notes",
                "group",
                "otp",
                "tags",
                "expires",
                "expiry_time",
                "custom_properties",
            ],
        )
        writer.writeheader()
        for entry in entries:
            custom = ";".join(
                f"{k}={v}" for k, v in sorted(entry.custom_properties.items())
            )
            writer.writerow(
                {
                    "title": entry.title,
                    "username": entry.username,
                    "password": entry.password,
                    "url": entry.url,
                    "notes": entry.notes,
                    "group": entry.group_path,
                    "otp": entry.otp,
                    "tags": ",".join(entry.tags),
                    "expires": "true" if entry.expires else "false",
                    "expiry_time": entry.expiry_time,
                    "custom_properties": custom,
                }
            )
        return atomic_write_private(target, handle.getvalue())
    finally:
        handle.close()
