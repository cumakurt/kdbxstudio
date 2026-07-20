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

    def _on_audit(self, report: object, **_: object) -> int:
        findings = getattr(report, "findings", ())
        count = sum(
            1 for f in findings if getattr(f, "kind", "") == "duplicate_password"
        )
        # Caller may not have context; return count for emit consumers.
        return count

    def activate(self, context: PluginContext) -> None:
        self._context = context

        def _wrapped(report: object, **kwargs: object) -> int:
            count = self._on_audit(report, **kwargs)
            context.set("duplicate_highlight.count", count)
            return count

        context.register_hook("audit.completed", _wrapped, owner=self.meta.name)
        context.set("duplicate_highlight.count", 0)

    def deactivate(self, context: PluginContext) -> None:
        context.clear_owner(self.meta.name)
        context.set("duplicate_highlight.count", 0)


def create_plugin() -> DuplicateHighlightPlugin:
    return DuplicateHighlightPlugin()
