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
    theme: str = "dark"  # ThemeMode value: system | dark | light | nord | …
    read_only: bool = False
    window_geometry: str = ""  # base64 of QByteArray
    window_state: str = ""  # base64 of QMainWindow.saveState()
    ui_density: str = "compact"  # compact | comfortable
    hibp_enabled: bool = False
    autotype_sequence: str = "{USERNAME}{TAB}{PASSWORD}{ENTER}"
    autotype_match_window: bool = True
    autotype_initial_delay_ms: int = 500
    watch_database_files: bool = True
    browser_integration_enabled: bool = True
    plugin_sha256_allowlist: tuple[str, ...] = ()
    check_updates_on_start: bool = True
    start_minimized_to_tray: bool = False
    language: str = "en"  # en | tr

    def with_updates(self, **kwargs: object) -> SecuritySettings:
        return replace(self, **kwargs)  # type: ignore[arg-type]
