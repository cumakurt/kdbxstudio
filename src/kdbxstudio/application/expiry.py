"""Shared entry expiry helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from kdbxstudio.core.database import EntryView

# Shared by audit dashboard and search filter chips.
EXPIRING_SOON_DAYS = 14


def parse_expiry(entry: EntryView) -> datetime | None:
    """Return timezone-aware UTC expiry instant, or None."""
    if not entry.expires or not entry.expiry_time:
        return None
    text = entry.expiry_time.strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except ValueError:
        return None


def local_date_to_utc_end_of_day(iso_date: str) -> datetime:
    """Interpret ``YYYY-MM-DD`` as local end-of-day, return UTC datetime."""
    day = date.fromisoformat(iso_date[:10])
    local_end = datetime.combine(day, time(23, 59, 59)).astimezone()
    return local_end.astimezone(UTC)


def expiry_local_date_iso(entry: EntryView) -> str | None:
    """Return the entry expiry as a local ``YYYY-MM-DD`` calendar date."""
    expiry = parse_expiry(entry)
    if expiry is None:
        return None
    local = expiry.astimezone()
    return local.date().isoformat()


def is_expired(entry: EntryView, *, now: datetime | None = None) -> bool:
    expiry = parse_expiry(entry)
    if expiry is None:
        return False
    current = now or datetime.now(UTC)
    return expiry <= current


def is_expiring_soon(
    entry: EntryView,
    *,
    now: datetime | None = None,
    days: int = EXPIRING_SOON_DAYS,
) -> bool:
    """True when expiry is in the future but within ``days``."""
    expiry = parse_expiry(entry)
    if expiry is None:
        return False
    current = now or datetime.now(UTC)
    if expiry <= current:
        return False
    return expiry <= current + timedelta(days=days)


@dataclass(frozen=True)
class ExpiryChipInfo:
    """Compact chip label + tone for expiry UI."""

    label: str
    tone: str  # danger | warning | success


def expiry_chip_info(
    entry: EntryView,
    *,
    now: datetime | None = None,
) -> ExpiryChipInfo | None:
    """Return chip text/tone for an expiring entry, or None when not applicable."""
    expiry = parse_expiry(entry)
    if expiry is None:
        return None
    current = now or datetime.now(UTC)
    delta = expiry - current
    days = delta.days
    if days < 0:
        return ExpiryChipInfo(label=f"{abs(days)}d ago", tone="danger")
    if days == 0:
        return ExpiryChipInfo(label="Today", tone="warning")
    if days <= EXPIRING_SOON_DAYS:
        return ExpiryChipInfo(label=f"{days}d", tone="warning")
    return ExpiryChipInfo(label=f"{days}d", tone="success")


def entry_list_tone(
    entry: EntryView,
    *,
    audit_tone: str | None = None,
    now: datetime | None = None,
) -> str | None:
    """Severity tone for entry list rows (expiry / recycle / optional audit)."""
    if entry.in_recycle_bin:
        return "muted"
    if is_expired(entry, now=now):
        return "danger"
    if is_expiring_soon(entry, now=now):
        return "warning"
    if audit_tone in ("danger", "warning", "success", "muted"):
        return audit_tone
    return None
