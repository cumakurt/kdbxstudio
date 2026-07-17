"""Merge entries from a source KDBX into a destination session."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kdbxstudio.application.expiry import parse_expiry
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


def _sync_attachments(
    destination: KdbxDatabase,
    dest_uuid: str,
    source: KdbxDatabase,
    source_uuid: str,
) -> None:
    for attachment in destination.list_attachments(dest_uuid):
        destination.delete_attachment(dest_uuid, attachment.id)
    for attachment in source.list_attachments(source_uuid):
        name = Path(attachment.filename).name or "attachment"
        destination.add_attachment(dest_uuid, name, attachment.data)


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
        expiry_time = parse_expiry(entry)
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
                otp=entry.otp,
                custom_properties=dict(entry.custom_properties),
                tags=list(entry.tags),
                expires=entry.expires,
                expiry_time=expiry_time,
            )
            _sync_attachments(destination, updated_entry.uuid, source, entry.uuid)
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
            expires=entry.expires if entry.expires or expiry_time else None,
            expiry_time=expiry_time,
        )
        if entry.otp:
            created = destination.update_entry(
                created.uuid, otp=entry.otp, keep_history=False
            )
        _sync_attachments(destination, created.uuid, source, entry.uuid)
        existing[sig] = created
        added += 1
    return MergeResult(added=added, skipped=skipped, updated=updated)
