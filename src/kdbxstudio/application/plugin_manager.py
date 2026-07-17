"""Plugin discovery and lifecycle manager."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from kdbxstudio.plugins.sdk import (
    LoadedPlugin,
    Plugin,
    PluginContext,
    PluginInfo,
    PluginMeta,
)


class PluginError(Exception):
    """Raised when a plugin fails to load or activate."""


class PluginManager:
    """Registers, discovers, and activates plugins."""

    def __init__(self, context: PluginContext | None = None) -> None:
        self._context = context or PluginContext()
        self._loaded: dict[str, LoadedPlugin] = {}

    @property
    def context(self) -> PluginContext:
        return self._context

    def register(self, plugin: Plugin, *, path: str | None = None) -> None:
        name = plugin.meta.name
        self._loaded[name] = LoadedPlugin(plugin=plugin, path=path)

    def unregister(self, name: str) -> None:
        if name in self._loaded and self._loaded[name].active:
            self.deactivate(name)
        self._loaded.pop(name, None)

    def activate(self, name: str) -> None:
        item = self._loaded[name]
        if item.active:
            return
        try:
            item.plugin.activate(self._context)
        except Exception as exc:
            raise PluginError(f"Failed to activate plugin '{name}': {exc}") from exc
        item.active = True

    def deactivate(self, name: str) -> None:
        item = self._loaded[name]
        if not item.active:
            return
        try:
            item.plugin.deactivate(self._context)
        except Exception as exc:
            raise PluginError(f"Failed to deactivate plugin '{name}': {exc}") from exc
        item.active = False

    def activate_all(self) -> None:
        for name in list(self._loaded):
            self.activate(name)

    def list_plugins(self) -> list[PluginInfo]:
        result: list[PluginInfo] = []
        for _name, item in sorted(self._loaded.items()):
            meta = item.plugin.meta
            result.append(
                PluginInfo(
                    name=meta.name,
                    version=meta.version,
                    description=meta.description,
                    active=item.active,
                    path=item.path,
                )
            )
        return result

    def discover(self, directory: Path | str) -> list[str]:
        """Load ``*_plugin.py`` modules that expose ``create_plugin()``."""
        root = Path(directory)
        if not root.is_dir():
            return []
        loaded_names: list[str] = []
        for path in sorted(root.glob("*_plugin.py")):
            name = self._load_from_path(path)
            if name:
                loaded_names.append(name)
        return loaded_names

    def _load_from_path(self, path: Path) -> str | None:
        module_name = f"kdbxstudio_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise PluginError(f"Cannot load plugin module: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            raise PluginError(f"Error importing {path}: {exc}") from exc
        factory = getattr(module, "create_plugin", None)
        if factory is None:
            return None
        plugin = factory()
        if not hasattr(plugin, "meta") or not isinstance(plugin.meta, PluginMeta):
            raise PluginError(f"Plugin in {path} missing PluginMeta")
        self.register(plugin, path=str(path))
        return plugin.meta.name
