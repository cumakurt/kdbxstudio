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
    """Replace destination attachments with source copies without delete-first.

    New binaries are added first; old destination attachments are removed only
    after the copy succeeds. On failure, newly added copies are rolled back.
    """
    source_attachments = source.list_attachments(source_uuid, include_data=True)
    old_ids = [
        attachment.id
        for attachment in destination.list_attachments(dest_uuid, include_data=False)
    ]
    added_ids: list[int] = []
    try:
        for attachment in source_attachments:
            name = Path(attachment.filename).name or "attachment"
            created = destination.add_attachment(dest_uuid, name, attachment.data)
            added_ids.append(created.id)
        for attachment_id in old_ids:
            destination.delete_attachment(dest_uuid, attachment_id)
    except Exception:
        for attachment_id in added_ids:
            try:
                destination.delete_attachment(dest_uuid, attachment_id)
            except Exception:
                pass
        raise


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
        _signature(e): e for e in destination.list_entries() if not e.in_recycle_bin
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
            expires=True if expiry_time else entry.expires,
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
