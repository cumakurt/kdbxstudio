"""Built-in sample plugin: tags audit findings in the plugin context."""

from __future__ import annotations

from kdbxstudio.plugins.sdk import PluginContext, PluginMeta


class DuplicateHighlightPlugin:
    """Example plugin that listens for audit reports."""

    meta = PluginMeta(
        name="duplicate-highlight",
        version="0.1.0",
        description="Counts duplicate-password findings from audit hooks",
        author="KDBXStudio",
    )

    def activate(self, context: PluginContext) -> None:
        context.register_hook("audit.completed", self._on_audit)
        context.set("duplicate_highlight.count", 0)

    def deactivate(self, context: PluginContext) -> None:
        context.set("duplicate_highlight.count", 0)

    def _on_audit(self, report: object, **_: object) -> int:
        findings = getattr(report, "findings", ())
        count = sum(
            1
            for f in findings
            if getattr(f, "kind", "") == "duplicate_password"
        )
        return count


def create_plugin() -> DuplicateHighlightPlugin:
    return DuplicateHighlightPlugin()
