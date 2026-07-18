"""Compare the installed KDBXStudio version with GitHub.

Resolution order (first success wins):
1. Latest published GitHub Release (`/releases/latest`)
2. Newest non-draft release from `/releases`
3. Newest semver-like git tag from `/tags`
4. Version declared on the default branch (`__init__.py` / `pyproject.toml`)
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_REPO = "cumakurt/kdbxstudio"
USER_AGENT = "KDBXStudio-update-check"


@dataclass(frozen=True)
class UpdateInfo:
    current: str
    latest: str
    newer: bool
    html_url: str
    tag: str
    source: str  # release | tag | repository
    equal: bool = False

    @property
    def status(self) -> str:
        if self.newer:
            return "update-available"
        if self.equal:
            return "up-to-date"
        return "ahead"  # local version newer than remote


def parse_version(text: str) -> tuple[int, ...]:
    """Extract a comparable numeric version tuple from a tag or version string."""
    cleaned = (text or "").strip().lstrip("vV")
    # Prefer dotted version before any suffix (1.2.3-rc1 → 1.2.3)
    match = re.search(r"(\d+(?:\.\d+)*)", cleaned)
    if not match:
        parts = re.findall(r"\d+", cleaned)
        return tuple(int(p) for p in parts) if parts else (0,)
    return tuple(int(p) for p in match.group(1).split("."))


def compare_versions(left: str, right: str) -> int:
    """Return -1 if left < right, 0 if equal, 1 if left > right."""
    a = parse_version(left)
    b = parse_version(right)
    # Pad to same length for 1.0 vs 1.0.0
    width = max(len(a), len(b))
    a = a + (0,) * (width - len(a))
    b = b + (0,) * (width - len(b))
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def _http_json(url: str, *, timeout_s: float) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_text(url: str, *, timeout_s: float) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read().decode("utf-8")


def _version_from_init(text: str) -> str | None:
    match = re.search(
        r"""^__version__\s*=\s*["']([^"']+)["']""",
        text,
        re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def _version_from_pyproject(text: str) -> str | None:
    match = re.search(
        r"""(?m)^version\s*=\s*["']([^"']+)["']""",
        text,
    )
    return match.group(1).strip() if match else None


def _info(
    *,
    current: str,
    latest: str,
    html_url: str,
    tag: str,
    source: str,
) -> UpdateInfo:
    cmp = compare_versions(current, latest)
    return UpdateInfo(
        current=current,
        latest=latest,
        newer=cmp < 0,
        equal=cmp == 0,
        html_url=html_url,
        tag=tag,
        source=source,
    )


def _from_release_payload(
    payload: dict[str, Any], *, current: str, repo: str
) -> UpdateInfo | None:
    tag = str(payload.get("tag_name") or "").strip()
    if not tag:
        return None
    latest = tag.lstrip("vV") or tag
    html_url = str(
        payload.get("html_url") or f"https://github.com/{repo}/releases/tag/{tag}"
    )
    return _info(
        current=current,
        latest=latest,
        html_url=html_url,
        tag=tag,
        source="release",
    )


def _check_latest_release(
    current: str, *, repo: str, timeout_s: float
) -> UpdateInfo | None:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        payload = _http_json(url, timeout_s=timeout_s)
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 403):
            return None
        raise
    if not isinstance(payload, dict):
        return None
    return _from_release_payload(payload, current=current, repo=repo)


def _check_releases_list(
    current: str, *, repo: str, timeout_s: float
) -> UpdateInfo | None:
    url = f"https://api.github.com/repos/{repo}/releases?per_page=20"
    try:
        payload = _http_json(url, timeout_s=timeout_s)
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 403):
            return None
        raise
    if not isinstance(payload, list):
        return None
    candidates: list[UpdateInfo] = []
    for item in payload:
        if not isinstance(item, dict) or item.get("draft"):
            continue
        info = _from_release_payload(item, current=current, repo=repo)
        if info is not None:
            candidates.append(info)
    if not candidates:
        return None
    return max(candidates, key=lambda i: parse_version(i.latest))


def _check_tags(current: str, *, repo: str, timeout_s: float) -> UpdateInfo | None:
    url = f"https://api.github.com/repos/{repo}/tags?per_page=30"
    try:
        payload = _http_json(url, timeout_s=timeout_s)
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 403):
            return None
        raise
    if not isinstance(payload, list):
        return None
    best: UpdateInfo | None = None
    for item in payload:
        if not isinstance(item, dict):
            continue
        tag = str(item.get("name") or "").strip()
        if not tag or parse_version(tag) == (0,):
            continue
        latest = tag.lstrip("vV") or tag
        info = _info(
            current=current,
            latest=latest,
            html_url=f"https://github.com/{repo}/releases/tag/{tag}",
            tag=tag,
            source="tag",
        )
        if best is None or parse_version(info.latest) > parse_version(best.latest):
            best = info
    return best


def _check_repository_files(
    current: str, *, repo: str, timeout_s: float
) -> UpdateInfo | None:
    """Read version from default-branch source when no releases/tags exist."""
    branches = ("main", "master")
    paths = (
        "src/kdbxstudio/__init__.py",
        "pyproject.toml",
    )
    for branch in branches:
        for path in paths:
            url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
            try:
                text = _http_text(url, timeout_s=timeout_s)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
                continue
            if path.endswith("__init__.py"):
                latest = _version_from_init(text)
            else:
                latest = _version_from_pyproject(text)
            if not latest:
                continue
            return _info(
                current=current,
                latest=latest,
                html_url=f"https://github.com/{repo}/tree/{branch}",
                tag=latest,
                source="repository",
            )
    return None


def check_github_release(
    current: str,
    *,
    repo: str = DEFAULT_REPO,
    timeout_s: float = 8.0,
) -> UpdateInfo:
    """Return version comparison against GitHub (releases → tags → repo files)."""
    errors: list[str] = []
    for checker in (
        _check_latest_release,
        _check_releases_list,
        _check_tags,
        _check_repository_files,
    ):
        try:
            info = checker(current, repo=repo, timeout_s=timeout_s)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            errors.append(str(exc))
            continue
        if info is not None:
            return info
    detail = "; ".join(errors) if errors else "no release, tag, or repository version found"
    raise RuntimeError(f"Update check failed: {detail}")


# Backward-compatible alias used by older call sites / docs
_parse_version = parse_version
