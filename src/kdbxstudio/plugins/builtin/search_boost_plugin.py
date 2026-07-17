"""Built-in sample plugin: search ranking hook stub."""

from __future__ import annotations

from kdbxstudio.plugins.sdk import PluginContext, PluginMeta


class SearchBoostPlugin:
    meta = PluginMeta(
        name="search-boost",
        version="0.1.0",
        description="Boosts search hit scores via the search.rank hook",
        author="KDBXStudio",
    )

    def activate(self, context: PluginContext) -> None:
        context.register_hook(
            "search.rank", self._boost, owner=self.meta.name
        )
        context.set("search_boost.enabled", True)

    def deactivate(self, context: PluginContext) -> None:
        context.clear_owner(self.meta.name)
        context.set("search_boost.enabled", False)

    def _boost(self, score: int = 0, **_: object) -> int:
        return int(score) + 1


def create_plugin() -> SearchBoostPlugin:
    return SearchBoostPlugin()
