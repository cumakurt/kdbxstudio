"""Load / save app preferences under XDG config."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path

from kdbxstudio.security.settings import SecuritySettings

_SETTINGS_VERSION = 4
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
    try:
        raw_clipboard = int(
            raw.get("clipboard_timeout_ms", SecuritySettings.clipboard_timeout_ms)
        )
        # 0 disables auto-clear; otherwise enforce a sane minimum.
        clipboard_ms = 0 if raw_clipboard <= 0 else max(1000, raw_clipboard)
    except (TypeError, ValueError):
        clipboard_ms = SecuritySettings.clipboard_timeout_ms
    try:
        autolock_ms = max(0, int(
            raw.get("auto_lock_timeout_ms", SecuritySettings.auto_lock_timeout_ms)
        ))
    except (TypeError, ValueError):
        autolock_ms = SecuritySettings.auto_lock_timeout_ms
    theme = str(raw.get("theme", SecuritySettings.theme))
    if theme not in ("dark", "light", "system"):
        theme = SecuritySettings.theme
    ui_density = str(raw.get("ui_density", SecuritySettings.ui_density))
    if ui_density not in ("compact", "comfortable"):
        ui_density = SecuritySettings.ui_density
    return SecuritySettings(
        clipboard_timeout_ms=clipboard_ms,
        auto_lock_timeout_ms=autolock_ms,
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
        theme=theme,
        read_only=bool(raw.get("read_only", SecuritySettings.read_only)),
        window_geometry=str(raw.get("window_geometry", "")),
        window_state=str(raw.get("window_state", "")),
        ui_density=ui_density,
        hibp_enabled=bool(raw.get("hibp_enabled", SecuritySettings.hibp_enabled)),
        autotype_sequence=str(
            raw.get("autotype_sequence", SecuritySettings.autotype_sequence)
        ),
        check_updates_on_start=bool(
            raw.get(
                "check_updates_on_start",
                SecuritySettings.check_updates_on_start,
            )
        ),
        start_minimized_to_tray=bool(
            raw.get(
                "start_minimized_to_tray",
                SecuritySettings.start_minimized_to_tray,
            )
        ),
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
        "read_only": settings.read_only,
        "window_geometry": settings.window_geometry,
        "window_state": settings.window_state,
        "ui_density": settings.ui_density,
        "hibp_enabled": settings.hibp_enabled,
        "autotype_sequence": settings.autotype_sequence,
        "check_updates_on_start": settings.check_updates_on_start,
        "start_minimized_to_tray": settings.start_minimized_to_tray,
        "recent_databases": recent_paths[:_MAX_RECENT],
    }
    data = json.dumps(payload, indent=2) + "\n"
    fd, tmp_path = tempfile.mkstemp(
        dir=target.parent, suffix=".tmp", prefix="settings."
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_path, target)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
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
