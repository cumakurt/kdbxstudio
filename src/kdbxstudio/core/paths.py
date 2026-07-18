"""Filesystem path helpers."""

from __future__ import annotations

import os
import stat
from pathlib import Path


def default_data_dir() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "kdbxstudio"
    return Path.home() / ".local" / "share" / "kdbxstudio"


def ensure_private_dir(path: Path | str) -> Path:
    """Create a directory with owner-only permissions (0700)."""
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(target, stat.S_IRWXU)
    except OSError:
        pass
    return target


def resolve_regular_file(path: Path | str) -> Path | None:
    """Return a resolved regular file path, or None for missing/symlink paths.

    Symlinks are rejected *before* resolve(), because Path.resolve() follows
    links and a post-resolve is_symlink() check would never trigger.
    """
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        return None
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None
    if resolved.is_symlink() or not resolved.is_file():
        return None
    return resolved
