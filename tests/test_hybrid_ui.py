"""Tests for expanded audit findings and search.rank hooks."""

from pathlib import Path

from kdbxstudio.application.audit_engine import AuditEngine
from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.application.search_engine import SearchEngine
from kdbxstudio.plugins.builtin.search_boost_plugin import create_plugin
from kdbxstudio.security.settings import SecuritySettings
from kdbxstudio.security.store import load_settings, save_settings
from kdbxstudio.ui.widgets.filter_bar import FilterBarWidget


def test_audit_entropy_and_username_findings(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "audit.kdbx", password="secret")
    root = mgr.root_group_uuid()
    # Length ≥8 but low charset variety → low entropy (not short-weak)
    mgr.add_entry(root, title="LowEnt", username="u1", password="aaaaaaaa")
    mgr.add_entry(root, title="NoUser", username="", password="StrongPass!23456")
    for i in range(3):
        mgr.add_entry(
            root,
            title=f"Shared{i}",
            username="sameuser",
            password=f"UniquePass!{i}23456",
        )

    report = AuditEngine(mgr).run()
    kinds = {f.kind for f in report.findings}
    assert "low_entropy" in kinds
    assert "missing_username" in kinds
    assert "reused_username" in kinds
    assert report.low_entropy >= 1
    assert report.missing_usernames >= 1
    assert report.reused_usernames >= 3
    assert report.severity_counts["info"] >= 1
    assert report.severity_counts["warning"] >= 1


def test_search_rank_hook_boosts_scores(tmp_path: Path) -> None:
    mgr = DatabaseManager()
    mgr.create(tmp_path / "rank.kdbx", password="secret")
    root = mgr.root_group_uuid()
    mgr.add_entry(root, title="Alpha Target", password="x")

    baseline = SearchEngine(mgr)
    base_hits = baseline.search("alpha")
    assert len(base_hits) == 1
    base_score = base_hits[0].score

    plugins = PluginManager()
    plugins.register(create_plugin())
    plugins.activate_all()
    boosted = SearchEngine(mgr)
    boosted.set_rank_emitter(plugins.context.emit)
    boost_hits = boosted.search("alpha")
    assert len(boost_hits) == 1
    assert boost_hits[0].score == base_score + 1


def test_layout_settings_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "layout.json"
    original = SecuritySettings(
        window_geometry="YWJjZA==",
        window_state="ZWZnaA==",
        theme="dark",
    )
    save_settings(original, path)
    loaded = load_settings(path)
    assert loaded.window_geometry == "YWJjZA=="
    assert loaded.window_state == "ZWZnaA=="


def test_filter_bar_chips_build_entry_filter(qtbot) -> None:
    bar = FilterBarWidget()
    qtbot.addWidget(bar)
    bar._has_url.setChecked(True)
    bar._weak.setChecked(True)
    bar._group.setText("Work")
    filt = bar.current_filter(query="vpn")
    assert filt.query == "vpn"
    assert filt.group_path_contains == "Work"
    assert filt.has_url is True
    assert filt.weak_only is True
    assert filt.empty_password is False
