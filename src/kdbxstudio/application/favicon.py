"""Favicon download and local cache for entry URLs."""

from __future__ import annotations

import hashlib
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def cache_dir() -> Path:
    root = Path.home() / ".cache" / "kdbxstudio" / "favicons"
    root.mkdir(parents=True, exist_ok=True)
    return root


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
    path = favicon_path_for_host(host)
    return path if path.is_file() and path.stat().st_size > 0 else None


def fetch_favicon(
    url: str, *, timeout_s: float = 6.0, max_bytes: int = 65536
) -> Path | None:
    """Download Google s2 favicon for the host; return local path or None."""
    host = normalize_host(url)
    if host is None:
        return None
    dest = favicon_path_for_host(host)
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    endpoint = f"https://www.google.com/s2/favicons?domain={host}&sz=32"
    req = urllib.request.Request(
        endpoint,
        headers={"User-Agent": "KDBXStudio/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = resp.read(max_bytes + 1)
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    if not data or len(data) > max_bytes:
        return None
    dest.write_bytes(data)
    return dest
