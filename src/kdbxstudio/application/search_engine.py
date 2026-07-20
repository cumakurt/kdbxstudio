"""Full-text search with an in-memory inverted index."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.core.database import EntryView

RankEmitter = Callable[..., list[Any]]

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

_FIELD_WEIGHTS = {
    "title": 10,
    "username": 6,
    "url": 5,
    "notes": 3,
    "group": 2,
    "custom": 4,
}


@dataclass(frozen=True)
class SearchHit:
    entry: EntryView
    score: int
    matched_fields: tuple[str, ...]


@dataclass
class _Posting:
    entry_uuid: str
    fields: set[str] = field(default_factory=set)


@dataclass
class EntryFilter:
    """Advanced filter constraints applied after / with search."""

    query: str = ""
    group_path_contains: str = ""
    tag_contains: str = ""
    has_url: bool | None = None
    has_otp_or_custom: bool | None = None
    in_recycle_bin: bool | None = False
    weak_only: bool = False
    empty_password: bool = False
    duplicates_only: bool = False
    expired_only: bool = False
    expiring_soon_only: bool = False
    min_password_length: int | None = None

    def is_empty(self) -> bool:
        return (
            not self.query.strip()
            and not self.group_path_contains.strip()
            and not self.tag_contains.strip()
            and self.has_url is None
            and self.has_otp_or_custom is None
            and self.in_recycle_bin is False
            and not self.weak_only
            and not self.empty_password
            and not self.duplicates_only
            and not self.expired_only
            and not self.expiring_soon_only
            and self.min_password_length is None
        )


class InvertedIndex:
    """Token → entry postings for one database session."""

    def __init__(self) -> None:
        self._postings: dict[str, dict[str, _Posting]] = defaultdict(dict)
        self._entries: dict[str, EntryView] = {}
        self._field_text: dict[str, dict[str, str]] = {}

    def clear(self) -> None:
        self._postings.clear()
        self._entries.clear()
        self._field_text.clear()

    def rebuild(self, entries: list[EntryView]) -> None:
        self.clear()
        for entry in entries:
            self._add_entry(entry)

    def _add_entry(self, entry: EntryView) -> None:
        self._entries[entry.uuid] = entry
        fields = {
            "title": entry.title or "",
            "username": entry.username or "",
            "url": entry.url or "",
            "notes": entry.notes or "",
            "group": entry.group_path or "",
            "tags": " ".join(entry.tags),
            "custom": " ".join(
                f"{k} {v}" for k, v in (entry.custom_properties or {}).items()
            ),
        }
        self._field_text[entry.uuid] = {k: v.lower() for k, v in fields.items()}
        for field_name, text in fields.items():
            for token in tokenize(text):
                bucket = self._postings[token]
                posting = bucket.get(entry.uuid)
                if posting is None:
                    posting = _Posting(entry_uuid=entry.uuid)
                    bucket[entry.uuid] = posting
                posting.fields.add(field_name)

    def field_texts(self, entry_uuid: str) -> dict[str, str]:
        return dict(self._field_text.get(entry_uuid, {}))

    def lookup(self, tokens: list[str]) -> dict[str, set[str]]:
        """Return entry_uuid → matched fields for documents containing all tokens."""
        if not tokens:
            return {}
        first = tokens[0]
        candidates = {
            uuid: set(posting.fields)
            for uuid, posting in self._postings.get(first, {}).items()
        }
        for token in tokens[1:]:
            next_map = self._postings.get(token, {})
            survivors: dict[str, set[str]] = {}
            for uuid, fields in candidates.items():
                posting = next_map.get(uuid)
                if posting is None:
                    continue
                survivors[uuid] = fields | set(posting.fields)
            candidates = survivors
            if not candidates:
                break
        return candidates


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")]


class SearchEngine:
    """Local full-text search backed by an inverted index per session."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self._dbm = database_manager
        self._indexes: dict[str, InvertedIndex] = {}
        self._rank_emitter: RankEmitter | None = None
        self._dbm.add_listener(self._on_db_changed)

    def set_rank_emitter(self, emitter: RankEmitter | None) -> None:
        """Optional plugin hook emitter for ``search.rank`` adjustments."""
        self._rank_emitter = emitter

    def invalidate(self, session_id: str | None = None) -> None:
        if session_id is None:
            self._indexes.clear()
            return
        self._indexes.pop(session_id, None)

    def search(
        self,
        query: str | EntryFilter = "",
        *,
        session_id: str | None = None,
        limit: int = 200,
        entry_filter: EntryFilter | None = None,
    ) -> list[SearchHit]:
        if isinstance(query, EntryFilter):
            if entry_filter is not None:
                raise TypeError(
                    "Pass EntryFilter as the first argument or entry_filter=, not both"
                )
            filt = query
            query_text = filt.query
        else:
            query_text = query
            filt = entry_filter or EntryFilter(query=query_text)
            if query_text and not filt.query:
                filt = EntryFilter(
                    query=query_text,
                    group_path_contains=filt.group_path_contains,
                    tag_contains=filt.tag_contains,
                    has_url=filt.has_url,
                    has_otp_or_custom=filt.has_otp_or_custom,
                    in_recycle_bin=filt.in_recycle_bin,
                    weak_only=filt.weak_only,
                    empty_password=filt.empty_password,
                    duplicates_only=filt.duplicates_only,
                    expired_only=filt.expired_only,
                    expiring_soon_only=filt.expiring_soon_only,
                    min_password_length=filt.min_password_length,
                )

        sid = session_id or self._dbm.active_id
        if sid is None:
            return []

        entries = self._dbm.all_entries(
            sid, include_recycle_bin=filt.in_recycle_bin is not False
        )
        entries = self._apply_filters(entries, filt)
        if not filt.query.strip():
            return [
                SearchHit(entry=e, score=0, matched_fields=()) for e in entries[:limit]
            ]

        index = self._ensure_index(sid)
        tokens = tokenize(filt.query)
        if not tokens:
            # Fallback substring for non-token queries
            return self._substring_search(entries, filt.query, limit)

        matched = index.lookup(tokens)
        hits: list[SearchHit] = []
        entry_by_uuid = {e.uuid: e for e in entries}
        q_lower = filt.query.strip().lower()
        for uuid, fields in matched.items():
            entry = entry_by_uuid.get(uuid)
            if entry is None:
                continue
            score = sum(_FIELD_WEIGHTS.get(f, 1) for f in fields)
            field_text = index.field_texts(uuid)
            for fname, text in field_text.items():
                if text.startswith(q_lower):
                    score += 4
                    fields.add(fname)
            score = self._adjust_score(score, entry, filt.query)
            hits.append(
                SearchHit(
                    entry=entry,
                    score=score,
                    matched_fields=tuple(sorted(fields)),
                )
            )
        hits.sort(key=lambda h: (-h.score, h.entry.title.lower()))
        return hits[:limit]

    def _adjust_score(self, score: int, entry: EntryView, query: str) -> int:
        if self._rank_emitter is None:
            return score
        results = self._rank_emitter(
            "search.rank", score=score, entry=entry, query=query
        )
        adjusted = score
        for result in results:
            if isinstance(result, (int, float)):
                adjusted = int(result)
        return adjusted

    def _substring_search(
        self, entries: list[EntryView], query: str, limit: int
    ) -> list[SearchHit]:
        q = query.strip().lower()
        hits: list[SearchHit] = []
        for entry in entries:
            matched: list[str] = []
            score = 0
            fields = {
                "title": entry.title,
                "username": entry.username,
                "url": entry.url,
                "notes": entry.notes,
                "group": entry.group_path,
            }
            for name, value in fields.items():
                text = (value or "").lower()
                if not text or q not in text:
                    continue
                matched.append(name)
                score += _FIELD_WEIGHTS.get(name, 1)
                if text.startswith(q):
                    score += 4
            if matched:
                score = self._adjust_score(score, entry, query)
                hits.append(
                    SearchHit(
                        entry=entry,
                        score=score,
                        matched_fields=tuple(matched),
                    )
                )
        hits.sort(key=lambda h: (-h.score, h.entry.title.lower()))
        return hits[:limit]

    def _apply_filters(
        self, entries: list[EntryView], filt: EntryFilter
    ) -> list[EntryView]:
        result = entries
        if filt.in_recycle_bin is False:
            result = [e for e in result if not e.in_recycle_bin]
        elif filt.in_recycle_bin is True:
            result = [e for e in result if e.in_recycle_bin]

        group_q = filt.group_path_contains.strip().lower()
        if group_q:
            result = [e for e in result if group_q in (e.group_path or "").lower()]

        tag_q = filt.tag_contains.strip().lower()
        if tag_q:
            result = [e for e in result if any(tag_q in t.lower() for t in e.tags)]

        if filt.has_url is True:
            result = [e for e in result if bool((e.url or "").strip())]
        elif filt.has_url is False:
            result = [e for e in result if not (e.url or "").strip()]

        if filt.has_otp_or_custom is True:
            result = [
                e
                for e in result
                if bool(e.custom_properties) or bool((e.otp or "").strip())
            ]
        elif filt.has_otp_or_custom is False:
            result = [
                e
                for e in result
                if not e.custom_properties and not (e.otp or "").strip()
            ]

        if filt.empty_password:
            result = [e for e in result if not (e.password or "")]

        if filt.weak_only:
            result = [e for e in result if e.password and len(e.password) < 8]

        if filt.expired_only:
            from kdbxstudio.application.expiry import is_expired

            result = [e for e in result if is_expired(e)]

        if filt.expiring_soon_only:
            from datetime import UTC, datetime

            from kdbxstudio.application.expiry import is_expiring_soon

            now = datetime.now(UTC)
            result = [e for e in result if is_expiring_soon(e, now=now)]

        if filt.min_password_length is not None:
            result = [
                e for e in result if len(e.password or "") >= filt.min_password_length
            ]

        if filt.duplicates_only:
            counts: dict[str, int] = defaultdict(int)
            for entry in result:
                if entry.password:
                    counts[entry.password] += 1
            result = [e for e in result if e.password and counts[e.password] > 1]

        return result

    def _ensure_index(self, session_id: str) -> InvertedIndex:
        index = self._indexes.get(session_id)
        if index is None:
            index = InvertedIndex()
            index.rebuild(self._dbm.all_entries(session_id))
            self._indexes[session_id] = index
        return index

    def _on_db_changed(self) -> None:
        # Rebuild lazily on next search
        self._indexes.clear()
