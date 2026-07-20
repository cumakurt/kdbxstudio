"""Tests for GitHub version / update checking."""

from __future__ import annotations

import io
import json
from urllib.error import HTTPError

import pytest

from kdbxstudio.application import update_check
from kdbxstudio.application.update_check import (
    check_github_release,
    compare_versions,
    parse_version,
)


def test_parse_version_strips_prefix_and_suffix() -> None:
    assert parse_version("v1.2.3") == (1, 2, 3)
    assert parse_version("1.0.0-rc1") == (1, 0, 0)
    assert parse_version("release-2.10") == (2, 10)


def test_compare_versions_pads_components() -> None:
    assert compare_versions("1.0", "1.0.0") == 0
    assert compare_versions("1.0.0", "1.0.1") == -1
    assert compare_versions("2.0.0", "1.9.9") == 1


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        if isinstance(payload, (dict, list)):
            data = json.dumps(payload).encode("utf-8")
        else:
            data = str(payload).encode("utf-8")
        self._buf = io.BytesIO(data)

    def read(self) -> bytes:
        return self._buf.read()

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_check_falls_back_to_repository_when_no_releases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_urlopen(req, timeout=8.0):  # noqa: ANN001
        url = req.full_url if hasattr(req, "full_url") else str(req)
        calls.append(url)
        if "releases/latest" in url or url.endswith("/releases?per_page=20"):
            raise HTTPError(url, 404, "Not Found", hdrs=None, fp=None)  # type: ignore[arg-type]
        if "/tags?" in url:
            return _FakeResponse([])
        if url.endswith("__init__.py"):
            return _FakeResponse('__version__ = "1.2.0"\n')
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(update_check.urllib.request, "urlopen", fake_urlopen)
    info = check_github_release("1.0.0")
    assert info.newer is True
    assert info.latest == "1.2.0"
    assert info.source == "repository"
    assert info.equal is False
    assert any("releases/latest" in u for u in calls)


def test_check_uses_latest_release(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout=8.0):  # noqa: ANN001
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "releases/latest" in url:
            return _FakeResponse(
                {
                    "tag_name": "v1.1.0",
                    "html_url": "https://github.com/cumakurt/kdbxstudio/releases/tag/v1.1.0",
                }
            )
        raise AssertionError(url)

    monkeypatch.setattr(update_check.urllib.request, "urlopen", fake_urlopen)
    info = check_github_release("1.1.0")
    assert info.equal is True
    assert info.newer is False
    assert info.source == "release"
    assert info.tag == "v1.1.0"


def test_check_uses_newest_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout=8.0):  # noqa: ANN001
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "releases/latest" in url or url.endswith("/releases?per_page=20"):
            raise HTTPError(url, 404, "Not Found", hdrs=None, fp=None)  # type: ignore[arg-type]
        if "/tags?" in url:
            return _FakeResponse(
                [{"name": "v0.9.0"}, {"name": "v1.3.0"}, {"name": "docs"}]
            )
        raise AssertionError(url)

    monkeypatch.setattr(update_check.urllib.request, "urlopen", fake_urlopen)
    info = check_github_release("1.0.0")
    assert info.latest == "1.3.0"
    assert info.source == "tag"
    assert info.newer is True


def test_live_github_repository_version() -> None:
    """Integration: repo has no releases yet; repository file fallback must work."""
    try:
        info = check_github_release("0.0.1", timeout_s=10.0)
    except RuntimeError as exc:
        pytest.skip(f"network unavailable: {exc}")
    assert info.latest
    assert parse_version(info.latest) >= (1, 0, 0)
    assert info.source in {"release", "tag", "repository"}
    assert info.newer is True
