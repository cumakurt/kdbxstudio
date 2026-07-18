"""Favicon download and local cache for entry URLs."""

from __future__ import annotations

import hashlib
import re
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from pathlib import Path
from urllib.parse import urlparse

_CACHE_DIR: Path | None = None
_FAVICON_HIT: dict[str, Path | None] = {}
_IN_FLIGHT: set[str] = set()
_IN_FLIGHT_LOCK = threading.Lock()
_PREFETCH_CAP = 40


def cache_dir() -> Path:
    global _CACHE_DIR
    if _CACHE_DIR is None:
        root = Path.home() / ".cache" / "kdbxstudio" / "favicons"
        root.mkdir(parents=True, exist_ok=True)
        _CACHE_DIR = root
    return _CACHE_DIR


def normalize_host(url: str) -> str | None:
    text = (url or "").strip()
    if not text:
        return None
    if "://" not in text:
        text = "https://" + text
    try:
        parsed = urlparse(text)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower().strip(".")
    if not host or not re.match(r"^[a-z0-9.-]+$", host):
        return None
    return host


def favicon_path_for_host(host: str) -> Path:
    digest = hashlib.sha256(host.encode("utf-8")).hexdigest()[:24]
    return cache_dir() / f"{digest}.ico"


def cached_favicon(url: str) -> Path | None:
    host = normalize_host(url)
    if host is None:
        return None
    if host in _FAVICON_HIT:
        return _FAVICON_HIT[host]
    path = favicon_path_for_host(host)
    hit = path if path.is_file() and path.stat().st_size > 0 else None
    _FAVICON_HIT[host] = hit
    return hit


def urls_missing_favicon(
    urls: Iterable[str], *, limit: int = _PREFETCH_CAP
) -> list[str]:
    """Return unique entry URLs that still need a favicon download."""
    missing: list[str] = []
    seen: set[str] = set()
    for url in urls:
        host = normalize_host(url)
        if host is None or host in seen:
            continue
        seen.add(host)
        if cached_favicon(url) is not None:
            continue
        missing.append(url.strip())
        if len(missing) >= limit:
            break
    return missing


def fetch_favicon(
    url: str, *, timeout_s: float = 6.0, max_bytes: int = 65536
) -> Path | None:
    """Download Google s2 favicon for the host; return local path or None."""
    host = normalize_host(url)
    if host is None:
        return None
    dest = favicon_path_for_host(host)
    if dest.is_file() and dest.stat().st_size > 0:
        _FAVICON_HIT[host] = dest
        return dest
    endpoint = f"https://www.google.com/s2/favicons?domain={host}&sz=64"
    req = urllib.request.Request(
        endpoint,
        headers={"User-Agent": "KDBXStudio/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = resp.read(max_bytes + 1)
    except (urllib.error.URLError, TimeoutError, OSError):
        _FAVICON_HIT[host] = None
        return None
    if not data or len(data) > max_bytes:
        _FAVICON_HIT[host] = None
        return None
    dest.write_bytes(data)
    _FAVICON_HIT[host] = dest
    return dest


def prefetch_favicons(
    urls: Iterable[str],
    *,
    on_done: Callable[[], None] | None = None,
    limit: int = _PREFETCH_CAP,
) -> None:
    """Background-fetch missing favicons for a batch of entry URLs."""
    pending = urls_missing_favicon(urls, limit=limit)
    if not pending:
        return

    def _worker() -> None:
        any_ok = False
        for url in pending:
            host = normalize_host(url)
            if host is None:
                continue
            with _IN_FLIGHT_LOCK:
                if host in _IN_FLIGHT:
                    continue
                _IN_FLIGHT.add(host)
            try:
                if fetch_favicon(url) is not None:
                    any_ok = True
            except Exception:
                pass
            finally:
                with _IN_FLIGHT_LOCK:
                    _IN_FLIGHT.discard(host)
        if any_ok and on_done is not None:
            on_done()

    threading.Thread(target=_worker, daemon=True).start()
