"""Panel registration for modular Security Dashboard reports."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from kdbxstudio.ui.security_dashboard.panel_base import DashboardPanel

PanelFactory = Callable[[], DashboardPanel]


@dataclass(frozen=True)
class PanelSpec:
    id: str
    title: str
    factory: PanelFactory
    span: int = 1  # relative width weight in the grid


_REGISTRY: list[PanelSpec] = []


def register_panel(
    panel_id: str,
    title: str,
    factory: PanelFactory,
    *,
    span: int = 1,
) -> None:
    _REGISTRY.append(PanelSpec(id=panel_id, title=title, factory=factory, span=span))


def registered_panels() -> tuple[PanelSpec, ...]:
    return tuple(_REGISTRY)


def clear_registry() -> None:
    """Test helper."""
    _REGISTRY.clear()
