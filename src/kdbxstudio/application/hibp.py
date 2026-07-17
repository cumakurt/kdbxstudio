"""Have I Been Pwned Pwned Passwords (k-anonymity) helper."""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path


class HibpError(Exception):
    """Raised when the HIBP API cannot be reached or returns an error."""


def _cache_path() -> Path:
    root = Path.home() / ".cache" / "kdbxstudio" / "hibp"
    root.mkdir(parents=True, exist_ok=True)
    return root / "prefix_cache.json"


def _load_cache() -> dict[str, dict[str, int]]:
    path = _cache_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            out: dict[str, dict[str, int]] = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    out[str(key)] = {str(a): int(b) for a, b in value.items()}
            return out
    except (OSError, ValueError, TypeError):
        return {}
    return {}


def _save_cache(cache: dict[str, dict[str, int]]) -> None:
    path = _cache_path()
    # Keep cache bounded.
    items = list(cache.items())[-200:]
    path.write_text(json.dumps(dict(items)), encoding="utf-8")


def password_sha1(password: str) -> str:
    digest = hashlib.sha1(
        password.encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()
    return digest.upper()


def fetch_range(prefix5: str, *, timeout_s: float = 8.0) -> dict[str, int]:
    """Return map of suffix→count for a 5-char SHA-1 prefix."""
    prefix5 = prefix5.upper()
    if len(prefix5) != 5 or any(c not in "0123456789ABCDEF" for c in prefix5):
        raise ValueError("prefix must be 5 hex chars")
    cache = _load_cache()
    if prefix5 in cache:
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
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise HibpError(f"HIBP request failed: {exc}") from exc
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
    try:
        _save_cache(cache)
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
