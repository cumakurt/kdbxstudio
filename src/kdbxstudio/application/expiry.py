"""Shared entry expiry helpers."""

from __future__ import annotations

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
    local_end = datetime.combine(day, time(23, 59, 59))
    return local_end.astimezone().astimezone(UTC)


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
