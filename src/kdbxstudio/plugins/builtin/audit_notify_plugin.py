"""Built-in sample plugin: records last audit time."""

from __future__ import annotations

from datetime import UTC, datetime

from kdbxstudio.plugins.sdk import PluginContext, PluginMeta


class AuditNotifyPlugin:
    meta = PluginMeta(
        name="audit-notify",
        version="0.1.0",
        description="Stores last audit summary timestamp in plugin context",
        author="KDBXStudio",
    )

    def activate(self, context: PluginContext) -> None:
        context.register_hook("audit.completed", self._on_audit)

    def deactivate(self, context: PluginContext) -> None:
        context.set("audit_notify.last", None)

    def _on_audit(self, report: object, **_: object) -> str:
        stamp = datetime.now(UTC).isoformat()
        return stamp


def create_plugin() -> AuditNotifyPlugin:
    return AuditNotifyPlugin()
