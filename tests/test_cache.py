"""Tests for Cache."""

import time

from kdbxstudio.core.cache import Cache


def test_cache_set_get() -> None:
    cache: Cache[str, int] = Cache()
    cache.set("a", 1)
    assert cache.get("a") == 1
    assert cache.get("missing") is None


def test_cache_ttl_expires() -> None:
    cache: Cache[str, str] = Cache(default_ttl=0.05)
    cache.set("x", "y")
    assert cache.get("x") == "y"
    time.sleep(0.08)
    assert cache.get("x") is None


def test_cache_contains_with_none_value() -> None:
    cache: Cache[str, str | None] = Cache()
    cache.set("nil", None)
    assert "nil" in cache
    assert cache.get("nil") is None
    assert "missing" not in cache
