"""Merge entries from a source KDBX into a destination session."""

from __future__ import annotations

from dataclasses import dataclass

from kdbxstudio.core.database import EntryView, KdbxDatabase


@dataclass(frozen=True)
class MergeResult:
    added: int
    skipped: int
    updated: int


def _signature(entry: EntryView) -> tuple[str, str, str]:
    return (
        (entry.title or "").strip().lower(),
        (entry.username or "").strip().lower(),
        (entry.url or "").strip().lower(),
    )


def merge_databases(
    destination: KdbxDatabase,
    source: KdbxDatabase,
    *,
    update_existing: bool = False,
) -> MergeResult:
    """Copy non-recycle-bin entries from source into destination.

    Matching uses (title, username, url). Groups are created by path.
    """
    existing = {
        _signature(e): e
        for e in destination.list_entries()
        if not e.in_recycle_bin
    }
    added = 0
    skipped = 0
    updated = 0
    for entry in source.list_entries():
        if entry.in_recycle_bin:
            continue
        sig = _signature(entry)
        if sig in existing:
            if not update_existing:
                skipped += 1
                continue
            current = existing[sig]
            updated_entry = destination.update_entry(
                current.uuid,
                title=entry.title,
                username=entry.username,
                password=entry.password,
                url=entry.url,
                notes=entry.notes,
                otp=entry.otp or None,
                custom_properties=dict(entry.custom_properties),
                tags=list(entry.tags),
            )
            existing[sig] = updated_entry
            updated += 1
            continue
        group_uuid = destination.ensure_group_path(entry.group_path or "Root")
        created = destination.add_entry(
            group_uuid,
            title=entry.title,
            username=entry.username,
            password=entry.password,
            url=entry.url,
            notes=entry.notes,
            custom_properties=dict(entry.custom_properties) or None,
            tags=list(entry.tags) or None,
        )
        if entry.otp:
            created = destination.update_entry(
                created.uuid, otp=entry.otp, keep_history=False
            )
        existing[sig] = created
        added += 1
    return MergeResult(added=added, skipped=skipped, updated=updated)
