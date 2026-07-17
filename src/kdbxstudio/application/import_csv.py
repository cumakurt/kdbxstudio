"""Import helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from kdbxstudio.core.database import KdbxDatabase


@dataclass(frozen=True)
class ImportResult:
    created: int
    skipped: int
    groups_created: int


def _parse_custom(raw: str) -> dict[str, str]:
    result: dict[str, str] = {}
    text = (raw or "").strip()
    if not text:
        return result
    for part in text.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        if key:
            result[key] = value
    return result


def import_entries_csv(
    database: KdbxDatabase,
    path: Path | str,
    *,
    default_group_uuid: str | None = None,
) -> ImportResult:
    """Import entries from a CSV previously written by export_entries_csv."""
    target = Path(path)
    created = 0
    skipped = 0
    groups_before = {g.uuid for g in database.list_groups()}
    root = default_group_uuid or database.root_group_uuid()

    with target.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return ImportResult(0, 0, 0)
        for row in reader:
            title = (row.get("title") or "").strip()
            if not title:
                skipped += 1
                continue
            group_path = (row.get("group") or "").strip()
            group_uuid = (
                database.ensure_group_path(group_path) if group_path else root
            )
            custom = _parse_custom(row.get("custom_properties") or "")
            entry = database.add_entry(
                group_uuid,
                title=title,
                username=row.get("username") or "",
                password=row.get("password") or "",
                url=row.get("url") or "",
                notes=row.get("notes") or "",
                custom_properties=custom or None,
            )
            otp = (row.get("otp") or "").strip()
            if otp:
                database.update_entry(entry.uuid, otp=otp, keep_history=False)
            created += 1

    groups_after = {g.uuid for g in database.list_groups()}
    return ImportResult(
        created=created,
        skipped=skipped,
        groups_created=len(groups_after - groups_before),
    )
