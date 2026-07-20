"""Load / save app preferences under XDG config."""

from __future__ import annotations

import json
import os
from pathlib import Path

from kdbxstudio.core.paths import atomic_write_private, ensure_private_dir
from kdbxstudio.i18n import normalize_language
from kdbxstudio.security.settings import SecuritySettings

_SETTINGS_VERSION = 7
_MAX_RECENT = 12
_MAX_TIMER_MS = 2_147_000_000


def _parse_bool(raw: object, default: bool) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, int) and raw in (0, 1):
        return bool(raw)
    if isinstance(raw, str):
        normalized = raw.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    return default


def _parse_int(
    raw: object,
    default: int,
    *,
    minimum: int = 0,
    maximum: int = _MAX_TIMER_MS,
) -> int:
    try:
        value = int(raw)  # type: ignore[call-overload]
    except (TypeError, ValueError, OverflowError):
        return default
    return max(minimum, min(maximum, value))


def _parse_sha_allowlist(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[str] = []
    for item in raw:
        text = str(item).strip().lower()
        if len(text) == 64 and all(c in "0123456789abcdef" for c in text):
            out.append(text)
    return tuple(out)


def default_config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return ensure_private_dir(Path(xdg) / "kdbxstudio")
    return ensure_private_dir(Path.home() / ".config" / "kdbxstudio")


def settings_path(config_dir: Path | None = None) -> Path:
    root = config_dir or default_config_dir()
    return root / "settings.json"


def load_settings(path: Path | None = None) -> SecuritySettings:
    target = path or settings_path()
    raw = _read_json(target)
    if not raw:
        return SecuritySettings()
    raw_clipboard = _parse_int(
        raw.get("clipboard_timeout_ms"),
        SecuritySettings.clipboard_timeout_ms,
    )
    # 0 disables auto-clear; otherwise enforce a sane minimum.
    clipboard_ms = 0 if raw_clipboard <= 0 else max(1000, raw_clipboard)
    autolock_ms = _parse_int(
        raw.get("auto_lock_timeout_ms"),
        SecuritySettings.auto_lock_timeout_ms,
    )
    theme = str(raw.get("theme", SecuritySettings.theme))
    from kdbxstudio.ui.theme.accent import VALID_ACCENT_IDS, parse_accent
    from kdbxstudio.ui.theme.tokens import VALID_THEME_IDS, parse_theme

    if theme not in VALID_THEME_IDS:
        theme = parse_theme(theme).value
    accent = str(raw.get("accent", SecuritySettings.accent))
    if accent not in VALID_ACCENT_IDS:
        accent = parse_accent(accent).value
    ui_density = str(raw.get("ui_density", SecuritySettings.ui_density))
    if ui_density not in ("compact", "comfortable"):
        ui_density = SecuritySettings.ui_density
    from kdbxstudio.ui.theme.geometry import (
        clamp_font_size,
        clamp_ui_scale_percent,
        normalize_menu_size,
        normalize_window_resolution,
    )

    ui_scale_percent = clamp_ui_scale_percent(
        raw.get("ui_scale_percent", SecuritySettings.ui_scale_percent)
    )
    font_size = clamp_font_size(raw.get("font_size", SecuritySettings.font_size))
    menu_size = normalize_menu_size(raw.get("menu_size", SecuritySettings.menu_size))
    window_resolution = normalize_window_resolution(
        raw.get("window_resolution", SecuritySettings.window_resolution)
    )
    language = normalize_language(str(raw.get("language", SecuritySettings.language)))
    custom_theme_path = str(
        raw.get("custom_theme_path", SecuritySettings.custom_theme_path)
    )
    dashboard_hidden_panels = str(
        raw.get(
            "dashboard_hidden_panels",
            SecuritySettings.dashboard_hidden_panels,
        )
    )
    return SecuritySettings(
        clipboard_timeout_ms=clipboard_ms,
        auto_lock_timeout_ms=autolock_ms,
        auto_lock_enabled=_parse_bool(
            raw.get("auto_lock_enabled"), SecuritySettings.auto_lock_enabled
        ),
        clear_clipboard_on_lock=_parse_bool(
            raw.get(
                "clear_clipboard_on_lock",
                SecuritySettings.clear_clipboard_on_lock,
            ),
            SecuritySettings.clear_clipboard_on_lock,
        ),
        minimize_on_lock=_parse_bool(
            raw.get("minimize_on_lock"), SecuritySettings.minimize_on_lock
        ),
        theme=theme,
        accent=accent,
        read_only=_parse_bool(raw.get("read_only"), SecuritySettings.read_only),
        window_geometry=str(raw.get("window_geometry", "")),
        window_state=str(raw.get("window_state", "")),
        ui_density=ui_density,
        ui_scale_percent=ui_scale_percent,
        font_size=font_size,
        menu_size=menu_size,
        window_resolution=window_resolution,
        hibp_enabled=_parse_bool(
            raw.get("hibp_enabled"), SecuritySettings.hibp_enabled
        ),
        favicon_downloads_enabled=_parse_bool(
            raw.get("favicon_downloads_enabled"),
            SecuritySettings.favicon_downloads_enabled,
        ),
        autotype_sequence=str(
            raw.get("autotype_sequence", SecuritySettings.autotype_sequence)
        ),
        autotype_match_window=_parse_bool(
            raw.get(
                "autotype_match_window",
                SecuritySettings.autotype_match_window,
            ),
            SecuritySettings.autotype_match_window,
        ),
        autotype_initial_delay_ms=_parse_int(
            raw.get("autotype_initial_delay_ms"),
            SecuritySettings.autotype_initial_delay_ms,
            maximum=60_000,
        ),
        watch_database_files=_parse_bool(
            raw.get(
                "watch_database_files",
                SecuritySettings.watch_database_files,
            ),
            SecuritySettings.watch_database_files,
        ),
        browser_integration_enabled=_parse_bool(
            raw.get(
                "browser_integration_enabled",
                SecuritySettings.browser_integration_enabled,
            ),
            SecuritySettings.browser_integration_enabled,
        ),
        plugin_sha256_allowlist=_parse_sha_allowlist(
            raw.get("plugin_sha256_allowlist", [])
        ),
        check_updates_on_start=_parse_bool(
            raw.get(
                "check_updates_on_start",
                SecuritySettings.check_updates_on_start,
            ),
            SecuritySettings.check_updates_on_start,
        ),
        start_minimized_to_tray=_parse_bool(
            raw.get(
                "start_minimized_to_tray",
                SecuritySettings.start_minimized_to_tray,
            ),
            SecuritySettings.start_minimized_to_tray,
        ),
        language=language,
        custom_theme_path=custom_theme_path,
        dashboard_hidden_panels=dashboard_hidden_panels,
    )


def save_settings(
    settings: SecuritySettings,
    path: Path | None = None,
    *,
    recent: list[str] | None = None,
) -> Path:
    target = path or settings_path()
    ensure_private_dir(target.parent)
    existing = _read_json(target) or {}
    recent_paths = (
        recent if recent is not None else list(existing.get("recent_databases", []))
    )
    payload = {
        "version": _SETTINGS_VERSION,
        "clipboard_timeout_ms": (
            0
            if settings.clipboard_timeout_ms <= 0
            else max(1000, settings.clipboard_timeout_ms)
        ),
        "auto_lock_timeout_ms": max(0, settings.auto_lock_timeout_ms),
        "auto_lock_enabled": settings.auto_lock_enabled,
        "clear_clipboard_on_lock": settings.clear_clipboard_on_lock,
        "minimize_on_lock": settings.minimize_on_lock,
        "theme": settings.theme,
        "accent": settings.accent,
        "read_only": settings.read_only,
        "window_geometry": settings.window_geometry,
        "window_state": settings.window_state,
        "ui_density": settings.ui_density,
        "ui_scale_percent": settings.ui_scale_percent,
        "font_size": settings.font_size,
        "menu_size": settings.menu_size,
        "window_resolution": settings.window_resolution,
        "hibp_enabled": settings.hibp_enabled,
        "favicon_downloads_enabled": settings.favicon_downloads_enabled,
        "autotype_sequence": settings.autotype_sequence,
        "autotype_match_window": settings.autotype_match_window,
        "autotype_initial_delay_ms": max(0, settings.autotype_initial_delay_ms),
        "watch_database_files": settings.watch_database_files,
        "browser_integration_enabled": settings.browser_integration_enabled,
        "plugin_sha256_allowlist": list(settings.plugin_sha256_allowlist),
        "check_updates_on_start": settings.check_updates_on_start,
        "start_minimized_to_tray": settings.start_minimized_to_tray,
        "language": settings.language,
        "custom_theme_path": settings.custom_theme_path,
        "dashboard_hidden_panels": settings.dashboard_hidden_panels,
        "recent_databases": recent_paths[:_MAX_RECENT],
    }
    data = json.dumps(payload, indent=2) + "\n"
    return atomic_write_private(target, data)


def load_recent_databases(path: Path | None = None) -> list[Path]:
    raw = _read_json(path or settings_path())
    if not raw:
        return []
    items = raw.get("recent_databases", [])
    if not isinstance(items, list):
        return []
    result: list[Path] = []
    for item in items:
        try:
            p = Path(str(item)).expanduser()
        except (TypeError, ValueError):
            continue
        result.append(p)
    return result


def remember_database(db_path: Path | str, path: Path | None = None) -> list[Path]:
    target = path or settings_path()
    resolved = str(Path(db_path).expanduser().resolve())
    recent = [str(p) for p in load_recent_databases(target)]
    recent = [resolved, *[p for p in recent if p != resolved]]
    settings = load_settings(target)
    save_settings(settings, target, recent=recent)
    return [Path(p) for p in recent[:_MAX_RECENT]]


def clear_recent_databases(path: Path | None = None) -> None:
    target = path or settings_path()
    settings = load_settings(target)
    save_settings(settings, target, recent=[])


def _read_json(target: Path) -> dict | None:
    if not target.is_file():
        return None
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None
