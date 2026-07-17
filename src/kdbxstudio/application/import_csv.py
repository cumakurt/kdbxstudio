"""Import helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from kdbxstudio.core.database import KdbxDatabase

_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "title": ("title", "name", "Title", "Name"),
    "username": (
        "username",
        "login_username",
        "login",
        "user",
        "Username",
        "Login Name",
    ),
    "password": ("password", "login_password", "Password"),
    "url": ("url", "login_uri", "uri", "Website", "URL"),
    "notes": ("notes", "Notes", "extra"),
    "group": ("group", "folder", "Group", "Folder"),
    "otp": ("otp", "totp", "TOTP", "login_totp"),
    "tags": ("tags", "Tags"),
    "expires": ("expires", "Expires"),
    "expiry_time": ("expiry_time", "expiry", "expire_time", "Expiry Date"),
    "custom_properties": ("custom_properties", "custom"),
}


@dataclass(frozen=True)
class ImportResult:
    created: int
    skipped: int
    groups_created: int


def _field(row: dict[str, str | None], logical: str) -> str:
    aliases = _COLUMN_ALIASES.get(logical, (logical,))
    for key in aliases:
        if key in row and row[key] is not None and str(row[key]).strip():
            return str(row[key]).strip()
    # Case-insensitive fallback
    lowered = {str(k).lower(): v for k, v in row.items() if k is not None}
    for key in aliases:
        value = lowered.get(key.lower())
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


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


def _parse_tags(raw: str) -> list[str]:
    if not raw.strip():
        return []
    if "," in raw:
        parts = raw.split(",")
    else:
        parts = raw.split(";")
    return [p.strip() for p in parts if p.strip()]


def import_entries_csv(
    database: KdbxDatabase,
    path: Path | str,
    *,
    default_group_uuid: str | None = None,
) -> ImportResult:
    """Import entries from CSV (native export or Bitwarden/Chrome-like aliases)."""
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
            # Normalize None values from DictReader
            normalized = {str(k): (v if v is not None else "") for k, v in row.items()}
            title = _field(normalized, "title")
            if not title:
                skipped += 1
                continue
            group_path = _field(normalized, "group")
            group_uuid = (
                database.ensure_group_path(group_path) if group_path else root
            )
            custom = _parse_custom(_field(normalized, "custom_properties"))
            tags = _parse_tags(_field(normalized, "tags"))
            expires_raw = _field(normalized, "expires").lower()
            expires = expires_raw in {"1", "true", "yes", "y"}
            expiry_raw = _field(normalized, "expiry_time")
            expiry_time: datetime | None = None
            if expiry_raw:
                try:
                    text = expiry_raw.strip()
                    if text.endswith("Z"):
                        text = text[:-1] + "+00:00"
                    expiry_time = datetime.fromisoformat(text)
                    expires = True
                except ValueError:
                    expiry_time = None
            entry = database.add_entry(
                group_uuid,
                title=title,
                username=_field(normalized, "username"),
                password=_field(normalized, "password"),
                url=_field(normalized, "url"),
                notes=_field(normalized, "notes"),
                custom_properties=custom or None,
                tags=tags or None,
                expires=expires if expires or expiry_time else None,
                expiry_time=expiry_time,
            )
            otp = _field(normalized, "otp")
            if otp:
                database.update_entry(entry.uuid, otp=otp, keep_history=False)
            created += 1

    groups_after = {g.uuid for g in database.list_groups()}
    return ImportResult(
        created=created,
        skipped=skipped,
        groups_created=len(groups_after - groups_before),
    )
