"""Built-in plugin marketplace catalog."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketplacePlugin:
    id: str
    name: str
    version: str
    description: str
    author: str
    builtin: bool
    module: str | None = None


CATALOG: tuple[MarketplacePlugin, ...] = (
    MarketplacePlugin(
        id="duplicate-highlight",
        name="Duplicate Highlight",
        version="0.1.0",
        description="Counts duplicate-password findings from audit hooks.",
        author="KDBXStudio",
        builtin=True,
        module="kdbxstudio.plugins.builtin.duplicate_highlight_plugin",
    ),
    MarketplacePlugin(
        id="audit-notify",
        name="Audit Notify",
        version="0.1.0",
        description="Stores last audit summary timestamp in plugin context.",
        author="KDBXStudio",
        builtin=True,
        module="kdbxstudio.plugins.builtin.audit_notify_plugin",
    ),
    MarketplacePlugin(
        id="search-boost",
        name="Search Boost",
        version="0.1.0",
        description="Registers a hook placeholder for future ranking tweaks.",
        author="KDBXStudio",
        builtin=True,
        module="kdbxstudio.plugins.builtin.search_boost_plugin",
    ),
)


def get_catalog() -> list[MarketplacePlugin]:
    return list(CATALOG)


def find_plugin(plugin_id: str) -> MarketplacePlugin | None:
    for item in CATALOG:
        if item.id == plugin_id:
            return item
    return None
