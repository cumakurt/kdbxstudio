"""Tests for roadmap Phase 0/1 foundations."""

from __future__ import annotations

from pathlib import Path

from kdbxstudio.application.autotype import (
    expand_sequence,
    find_best_entry_for_window,
    score_entry_for_window,
)
from kdbxstudio.application.browser_bridge import (
    BrowserBridgeServer,
    BrowserVaultSnapshot,
    match_logins_for_url,
    url_host,
)
from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.core.database import EntryView
from kdbxstudio.plugins.sdk import PluginContext


def _entry(**kwargs) -> EntryView:
    base = dict(
        uuid="u1",
        title="GitHub",
        username="user",
        password="secret",
        url="https://github.com/login",
        notes="",
        group_path="Root",
    )
    base.update(kwargs)
    return EntryView(**base)


def test_expand_sequence_supports_delay_ms() -> None:
    steps = expand_sequence(
        "{USERNAME}{DELAY=500}{PASSWORD}",
        username="a",
        password="b",
    )
    assert ("delay", "500") in steps
    assert ("type", "a") in steps
    assert ("type", "b") in steps


def test_window_match_prefers_url_host() -> None:
    entry = _entry()
    match = score_entry_for_window(entry, "GitHub — Mozilla Firefox")
    assert match is not None
    assert match.score >= 55
    best = find_best_entry_for_window(
        [entry, _entry(uuid="u2", title="Other", url="")],
        "Sign in to GitHub",
    )
    assert best is not None
    assert best.entry.uuid == "u1"


def test_browser_url_host_and_logins() -> None:
    assert url_host("https://www.Example.com/path") == "example.com"
    hits = match_logins_for_url(
        [_entry(), _entry(uuid="u2", url="https://gitlab.com")],
        "https://github.com/foo",
    )
    assert [h.uuid for h in hits] == ["u1"]


def test_browser_bridge_ping_and_logins(tmp_path: Path, monkeypatch) -> None:
    sock = tmp_path / "browser.sock"
    monkeypatch.setattr(
        "kdbxstudio.application.browser_bridge.browser_socket_path",
        lambda: sock,
    )
    snapshot = BrowserVaultSnapshot(
        database_hash="abc",
        entries=[_entry()],
    )
    server = BrowserBridgeServer(lambda: snapshot)
    server.start()
    try:
        assert server.handle_request({"action": "ping"})["success"] is True
        hashed = server.handle_request({"action": "get-databasehash"})
        assert hashed["hash"] == "abc"
        logins = server.handle_request(
            {"action": "get-logins", "url": "https://github.com"}
        )
        assert logins["success"] is True
        assert logins["entries"][0]["login"] == "user"
    finally:
        server.stop()


def test_plugin_allowlist_blocks_unknown(tmp_path: Path) -> None:
    plugin_path = tmp_path / "demo_plugin.py"
    plugin_path.write_text(
        "from kdbxstudio.plugins.sdk import Plugin, PluginMeta\n"
        "class _P(Plugin):\n"
        "    meta = PluginMeta(name='demo', version='1', description='d')\n"
        "    def activate(self, context): pass\n"
        "    def deactivate(self, context): pass\n"
        "def create_plugin():\n"
        "    return _P()\n",
        encoding="utf-8",
    )
    mgr = PluginManager(PluginContext())
    assert mgr.discover(tmp_path) == []
    assert mgr.discover(tmp_path, allow_unverified=True) == ["demo"]
    mgr2 = PluginManager(PluginContext())
    blocked = mgr2.discover(
        tmp_path,
        sha256_allowlist=("0" * 64,),
    )
    assert blocked == []
