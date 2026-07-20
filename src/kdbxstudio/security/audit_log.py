"""Best-effort security event log (no secrets)."""

from __future__ import annotations

import json
import os
import stat
import threading
from datetime import UTC, datetime
from pathlib import Path

from kdbxstudio.core.paths import (
    atomic_write_private,
    default_data_dir,
    ensure_private_dir,
)

_lock = threading.Lock()
_MAX_LINES = 2_000


def audit_log_path() -> Path:
    return ensure_private_dir(default_data_dir() / "logs") / "security.jsonl"


def log_security_event(event: str, **fields: object) -> None:
    """Append a JSON line describing a security-relevant action.

    Callers must never pass passwords, key material, or TOTP secrets.
    """
    payload = {
        "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "event": event,
        **{k: v for k, v in fields.items() if v is not None},
    }
    line = json.dumps(payload, separators=(",", ":"), default=str) + "\n"
    path = audit_log_path()
    with _lock:
        try:
            flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(path, flags, stat.S_IRUSR | stat.S_IWUSR)
            with os.fdopen(fd, "a", encoding="utf-8") as handle:
                handle.write(line)
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            _trim_if_needed(path)
        except OSError:
            pass


def _trim_if_needed(path: Path) -> None:
    try:
        raw = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    if len(raw) <= _MAX_LINES:
        return
    atomic_write_private(path, "\n".join(raw[-_MAX_LINES:]) + "\n")
