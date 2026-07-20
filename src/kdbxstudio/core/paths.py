"""Filesystem path helpers."""

from __future__ import annotations

import os
import stat
import tempfile
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


def fsync_parent_directory(path: Path | str) -> None:
    """Best-effort sync of a file's parent after an atomic rename."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(Path(path).parent, flags)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_private(
    path: Path | str,
    data: str | bytes,
    *,
    encoding: str = "utf-8",
) -> Path:
    """Atomically replace *path* with an owner-only (0600) regular file.

    The temporary file is created in the destination directory so ``os.replace``
    is atomic.  Writing to a temporary file also avoids following a destination
    symlink and prevents plaintext exports from briefly inheriting a permissive
    process umask.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = data.encode(encoding) if isinstance(data, str) else data
    fd, raw_tmp = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(raw_tmp)
    try:
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
        os.chmod(target, stat.S_IRUSR | stat.S_IWUSR)
        fsync_parent_directory(target)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return target
