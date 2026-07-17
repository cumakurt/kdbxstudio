"""Tests for marketplace catalog and standard icons."""

from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.plugins.marketplace import find_plugin, get_catalog
from kdbxstudio.plugins.sdk import PluginContext
from kdbxstudio.ui.icons import ICON_OPEN, standard_icon


def test_marketplace_catalog() -> None:
    catalog = get_catalog()
    assert len(catalog) >= 3
    plugin = find_plugin("duplicate-highlight")
    assert plugin is not None
    assert plugin.builtin is True


def test_marketplace_install_activate() -> None:
    mgr = PluginManager(PluginContext())
    entry = find_plugin("search-boost")
    assert entry is not None and entry.module
    import importlib

    module = importlib.import_module(entry.module)
    plugin = module.create_plugin()
    mgr.register(plugin)
    mgr.activate(entry.id)
    assert any(p.active for p in mgr.list_plugins() if p.name == entry.id)


def test_standard_icon_available(qtbot) -> None:
    icon = standard_icon(ICON_OPEN)
    assert not icon.isNull()
