"""Have I Been Pwned Pwned Passwords (k-anonymity) helper."""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from collections import OrderedDict
from pathlib import Path

from kdbxstudio.core.paths import atomic_write_private, ensure_private_dir

_MAX_CACHE_ENTRIES = 200
_FLUSH_EVERY = 8
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024

# Process-local prefix cache (avoids re-reading JSON on every lookup).
_memory_cache: OrderedDict[str, dict[str, int]] | None = None
_dirty_writes = 0


class HibpError(Exception):
    """Raised when the HIBP API cannot be reached or returns an error."""


def _cache_path() -> Path:
    root = ensure_private_dir(Path.home() / ".cache" / "kdbxstudio" / "hibp")
    return root / "prefix_cache.json"


def _load_cache() -> OrderedDict[str, dict[str, int]]:
    path = _cache_path()
    out: OrderedDict[str, dict[str, int]] = OrderedDict()
    if not path.is_file():
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    out[str(key)] = {str(a): int(b) for a, b in value.items()}
    except (OSError, ValueError, TypeError):
        return OrderedDict()
    return out


def _save_cache(cache: OrderedDict[str, dict[str, int]]) -> None:
    path = _cache_path()
    # Bound size (LRU: oldest keys first in OrderedDict).
    while len(cache) > _MAX_CACHE_ENTRIES:
        cache.popitem(last=False)
    atomic_write_private(path, json.dumps(dict(cache)))


def _get_memory_cache() -> OrderedDict[str, dict[str, int]]:
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = _load_cache()
    return _memory_cache


def reset_hibp_cache_for_tests() -> None:
    """Clear in-memory HIBP cache (tests only)."""
    global _memory_cache, _dirty_writes
    _memory_cache = None
    _dirty_writes = 0


def password_sha1(password: str) -> str:
    digest = hashlib.sha1(
        password.encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()
    return digest.upper()


def fetch_range(prefix5: str, *, timeout_s: float = 8.0) -> dict[str, int]:
    """Return map of suffix→count for a 5-char SHA-1 prefix."""
    global _dirty_writes
    prefix5 = prefix5.upper()
    if len(prefix5) != 5 or any(c not in "0123456789ABCDEF" for c in prefix5):
        raise ValueError("prefix must be 5 hex chars")
    cache = _get_memory_cache()
    if prefix5 in cache:
        cache.move_to_end(prefix5)
        return cache[prefix5]
    url = f"https://api.pwnedpasswords.com/range/{prefix5}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "KDBXStudio/1.0 (password health; k-anonymity)",
            "Add-Padding": "true",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read(_MAX_RESPONSE_BYTES + 1)
    except urllib.error.URLError as exc:
        raise HibpError(f"HIBP request failed: {exc}") from exc
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise HibpError("HIBP response exceeded the 2 MiB safety limit")
    body = raw.decode("utf-8", errors="replace")
    mapping: dict[str, int] = {}
    for line in body.splitlines():
        if ":" not in line:
            continue
        suffix, count_s = line.split(":", 1)
        try:
            mapping[suffix.strip().upper()] = int(count_s.strip())
        except ValueError:
            continue
    cache[prefix5] = mapping
    cache.move_to_end(prefix5)
    _dirty_writes += 1
    if _dirty_writes >= _FLUSH_EVERY:
        try:
            _save_cache(cache)
            _dirty_writes = 0
        except OSError:
            pass
    return mapping


def pwned_count(password: str, *, timeout_s: float = 8.0) -> int:
    """Return how many times ``password`` appears in HIBP (0 if not found)."""
    if not password:
        return 0
    digest = password_sha1(password)
    prefix, suffix = digest[:5], digest[5:]
    mapping = fetch_range(prefix, timeout_s=timeout_s)
    return int(mapping.get(suffix, 0))
