"""Load / save app preferences under XDG config."""

from __future__ import annotations

import json
import os
from pathlib import Path

from kdbxstudio.security.settings import SecuritySettings

_SETTINGS_VERSION = 3
_MAX_RECENT = 12


def default_config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "kdbxstudio"
    return Path.home() / ".config" / "kdbxstudio"


def settings_path(config_dir: Path | None = None) -> Path:
    root = config_dir or default_config_dir()
    return root / "settings.json"


def load_settings(path: Path | None = None) -> SecuritySettings:
    target = path or settings_path()
    raw = _read_json(target)
    if not raw:
        return SecuritySettings()
    return SecuritySettings(
        clipboard_timeout_ms=int(
            raw.get("clipboard_timeout_ms", SecuritySettings.clipboard_timeout_ms)
        ),
        auto_lock_timeout_ms=int(
            raw.get("auto_lock_timeout_ms", SecuritySettings.auto_lock_timeout_ms)
        ),
        auto_lock_enabled=bool(
            raw.get("auto_lock_enabled", SecuritySettings.auto_lock_enabled)
        ),
        clear_clipboard_on_lock=bool(
            raw.get(
                "clear_clipboard_on_lock",
                SecuritySettings.clear_clipboard_on_lock,
            )
        ),
        minimize_on_lock=bool(
            raw.get("minimize_on_lock", SecuritySettings.minimize_on_lock)
        ),
        theme=str(raw.get("theme", SecuritySettings.theme)),
        read_only=bool(raw.get("read_only", SecuritySettings.read_only)),
        window_geometry=str(raw.get("window_geometry", "")),
        window_state=str(raw.get("window_state", "")),
    )


def save_settings(
    settings: SecuritySettings,
    path: Path | None = None,
    *,
    recent: list[str] | None = None,
) -> Path:
    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_json(target) or {}
    recent_paths = (
        recent if recent is not None else list(existing.get("recent_databases", []))
    )
    payload = {
        "version": _SETTINGS_VERSION,
        "clipboard_timeout_ms": settings.clipboard_timeout_ms,
        "auto_lock_timeout_ms": settings.auto_lock_timeout_ms,
        "auto_lock_enabled": settings.auto_lock_enabled,
        "clear_clipboard_on_lock": settings.clear_clipboard_on_lock,
        "minimize_on_lock": settings.minimize_on_lock,
        "theme": settings.theme,
        "read_only": settings.read_only,
        "window_geometry": settings.window_geometry,
        "window_state": settings.window_state,
        "recent_databases": recent_paths[:_MAX_RECENT],
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


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
