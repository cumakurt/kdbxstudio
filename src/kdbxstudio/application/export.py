"""Export helpers."""

from __future__ import annotations

import csv
from pathlib import Path

from kdbxstudio.core.database import EntryView


def export_entries_csv(path: Path | str, entries: list[EntryView]) -> Path:
    """Write entries to a CSV file (passwords included — handle carefully)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
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
                    "custom_properties": custom,
                }
            )
    return target
