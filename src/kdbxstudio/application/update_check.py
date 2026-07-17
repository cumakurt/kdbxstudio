"""Check GitHub Releases for a newer KDBXStudio version."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateInfo:
    current: str
    latest: str
    newer: bool
    html_url: str
    tag: str


def _parse_version(text: str) -> tuple[int, ...]:
    cleaned = text.strip().lstrip("vV")
    parts = re.findall(r"\d+", cleaned)
    return tuple(int(p) for p in parts) if parts else (0,)


def check_github_release(
    current: str,
    *,
    repo: str = "cumakurt/kdbxstudio",
    timeout_s: float = 8.0,
) -> UpdateInfo:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "KDBXStudio-update-check",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Update check failed: {exc}") from exc
    tag = str(payload.get("tag_name") or "")
    html_url = str(payload.get("html_url") or f"https://github.com/{repo}/releases")
    latest = tag.lstrip("vV") or tag
    newer = _parse_version(latest) > _parse_version(current)
    return UpdateInfo(
        current=current,
        latest=latest or current,
        newer=newer,
        html_url=html_url,
        tag=tag,
    )
