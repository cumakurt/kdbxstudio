"""Simple in-memory cache with optional TTL."""

from __future__ import annotations

import time
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


@dataclass
class _CacheEntry(Generic[V]):
    value: V
    expires_at: float | None


class Cache(Generic[K, V]):
    """Thread-unsafe dict cache with optional per-entry TTL (seconds)."""

    def __init__(self, default_ttl: float | None = None) -> None:
        self._default_ttl = default_ttl
        self._store: dict[K, _CacheEntry[V]] = {}

    def get(self, key: K, default: V | None = None) -> V | None:
        entry = self._store.get(key)
        if entry is None:
            return default
        if entry.expires_at is not None and time.monotonic() >= entry.expires_at:
            del self._store[key]
            return default
        return entry.value

    def set(self, key: K, value: V, ttl: float | None = None) -> None:
        effective_ttl = self._default_ttl if ttl is None else ttl
        expires_at = (
            None if effective_ttl is None else time.monotonic() + effective_ttl
        )
        self._store[key] = _CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: K) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, Hashable):
            return False
        return self.get(key) is not None  # type: ignore[arg-type]

    def __len__(self) -> int:
        self._purge_expired()
        return len(self._store)

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired = [
            key
            for key, entry in self._store.items()
            if entry.expires_at is not None and now >= entry.expires_at
        ]
        for key in expired:
            del self._store[key]


class EntryIndexCache(Cache[str, Any]):
    """Cache for search / entry index payloads."""

    def __init__(self) -> None:
        super().__init__(default_ttl=None)
