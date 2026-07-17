"""Application security preferences."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class SecuritySettings:
    """User-configurable security options."""

    clipboard_timeout_ms: int = 15_000
    auto_lock_timeout_ms: int = 5 * 60_000
    auto_lock_enabled: bool = True
    clear_clipboard_on_lock: bool = True
    minimize_on_lock: bool = False
    theme: str = "dark"  # system | light | dark
    read_only: bool = False
    window_geometry: str = ""  # base64 of QByteArray
    window_state: str = ""  # base64 of QMainWindow.saveState()
    ui_density: str = "compact"  # compact | comfortable
    hibp_enabled: bool = False
    autotype_sequence: str = "{USERNAME}{TAB}{PASSWORD}{ENTER}"
    check_updates_on_start: bool = True
    start_minimized_to_tray: bool = False

    def with_updates(self, **kwargs: object) -> SecuritySettings:
        return replace(self, **kwargs)  # type: ignore[arg-type]
