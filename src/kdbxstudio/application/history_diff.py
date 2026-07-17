"""Compare two history snapshots field-by-field."""

from __future__ import annotations

from dataclasses import dataclass

from kdbxstudio.core.database import EntryView, HistoryView


@dataclass(frozen=True)
class FieldDiff:
    field: str
    before: str
    after: str


def _mask(value: str, *, secret: bool) -> str:
    if not secret:
        return value
    if not value:
        return ""
    return "••••••••"


def diff_history(
    before: HistoryView | EntryView,
    after: HistoryView | EntryView,
    *,
    mask_secrets: bool = True,
) -> list[FieldDiff]:
    pairs = [
        ("title", before.title, after.title, False),
        ("username", before.username, after.username, False),
        ("password", before.password, after.password, True),
        ("url", before.url, after.url, False),
        ("notes", before.notes, after.notes, False),
        ("otp", before.otp, after.otp, True),
    ]
    if isinstance(before, EntryView) and isinstance(after, EntryView):
        before_tags = sorted(before.tags) if before.tags else []
        after_tags = sorted(after.tags) if after.tags else []
        before_custom = sorted(
            f"{k}={v}" for k, v in (before.custom_properties or {}).items()
        )
        after_custom = sorted(
            f"{k}={v}" for k, v in (after.custom_properties or {}).items()
        )
        before_expiry = before.expiry_time or ""
        after_expiry = after.expiry_time or ""
        pairs.extend([
            ("tags", " ".join(before_tags), " ".join(after_tags), False),
            ("custom", " ".join(before_custom), " ".join(after_custom), False),
            ("expiry", before_expiry, after_expiry, False),
        ])
    diffs: list[FieldDiff] = []
    for name, left, right, secret in pairs:
        if (left or "") == (right or ""):
            continue
        diffs.append(
            FieldDiff(
                field=name,
                before=_mask(left or "", secret=secret and mask_secrets),
                after=_mask(right or "", secret=secret and mask_secrets),
            )
        )
    return diffs
