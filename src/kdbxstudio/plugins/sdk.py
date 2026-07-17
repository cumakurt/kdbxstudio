"""Plugin SDK contracts and context."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class PluginMeta:
    name: str
    version: str
    description: str = ""
    author: str = ""


class PluginContext:
    """Services exposed to plugins (kept intentionally small)."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[tuple[str | None, Callable[..., Any]]]] = {}
        self._data: dict[str, Any] = {}

    def register_hook(
        self,
        name: str,
        callback: Callable[..., Any],
        *,
        owner: str | None = None,
    ) -> None:
        self._hooks.setdefault(name, []).append((owner, callback))

    def clear_owner(self, owner: str) -> None:
        for name, items in list(self._hooks.items()):
            kept = [(o, cb) for o, cb in items if o != owner]
            if kept:
                self._hooks[name] = kept
            else:
                self._hooks.pop(name, None)

    def emit(self, name: str, **payload: Any) -> list[Any]:
        results: list[Any] = []
        for _owner, callback in self._hooks.get(name, []):
            try:
                results.append(callback(**payload))
            except Exception:
                results.append(None)
        return results

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


class Plugin(Protocol):
    """Plugin contract."""

    meta: PluginMeta

    def activate(self, context: PluginContext) -> None: ...

    def deactivate(self, context: PluginContext) -> None: ...


@dataclass
class PluginInfo:
    name: str
    version: str
    description: str
    active: bool
    path: str | None = None


@dataclass
class LoadedPlugin:
    plugin: Plugin
    path: str | None = None
    active: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
