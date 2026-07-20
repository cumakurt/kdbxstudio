"""SSH agent helpers (OpenSSH ssh-add)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class SshAgentError(Exception):
    """Raised when ssh-add cannot be run."""


_COMMAND_TIMEOUT_S = 15


def agent_available() -> bool:
    return bool(shutil.which("ssh-add") and os.environ.get("SSH_AUTH_SOCK"))


def _shred_and_unlink(path: Path) -> None:
    try:
        if path.is_file():
            size = path.stat().st_size
            with path.open("r+b") as handle:
                handle.write(b"\0" * size)
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except OSError:
                    pass
        path.unlink(missing_ok=True)
    except OSError:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def add_private_key(pem_text: str, *, lifetime_seconds: int | None = None) -> str:
    """Load a PEM/OpenSSH private key into the agent. Returns ssh-add stdout."""
    if not shutil.which("ssh-add"):
        raise SshAgentError("ssh-add not found on PATH")
    if not os.environ.get("SSH_AUTH_SOCK"):
        raise SshAgentError("SSH_AUTH_SOCK is not set (agent not running)")
    pem = pem_text.strip() + "\n"
    cmd = ["ssh-add"]
    if lifetime_seconds is not None and lifetime_seconds > 0:
        cmd.extend(["-t", str(lifetime_seconds)])
    # Prefer stdin to avoid leaving the key on disk.
    cmd.append("-")
    try:
        proc = subprocess.run(
            cmd,
            input=pem,
            capture_output=True,
            text=True,
            check=False,
            timeout=_COMMAND_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        raise SshAgentError("ssh-add timed out") from None
    if proc.returncode == 0:
        return (proc.stdout or proc.stderr or "Identity added.").strip()

    # Fallback for agents that reject stdin ("-"): create 0600 tempfile.
    fd, name = tempfile.mkstemp(prefix="kdbxstudio-ssh-", suffix=".pem")
    path = Path(name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as handle:
            handle.write(pem)
        file_cmd = ["ssh-add"]
        if lifetime_seconds is not None and lifetime_seconds > 0:
            file_cmd.extend(["-t", str(lifetime_seconds)])
        file_cmd.append(str(path))
        try:
            proc = subprocess.run(
                file_cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=_COMMAND_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            raise SshAgentError("ssh-add timed out") from None
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or "ssh-add failed"
            raise SshAgentError(detail)
        return (proc.stdout or proc.stderr or "Identity added.").strip()
    finally:
        _shred_and_unlink(path)
