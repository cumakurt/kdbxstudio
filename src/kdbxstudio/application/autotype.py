"""Linux Auto-Type helper (xdotool / ydotool / wtype)."""

from __future__ import annotations

import shutil
import subprocess
import time


class AutoTypeError(Exception):
    """Raised when no suitable typer backend is available."""


def detect_backend() -> str | None:
    for name in ("xdotool", "ydotool", "wtype"):
        if shutil.which(name):
            return name
    return None


def _type_xdotool(text: str) -> None:
    subprocess.run(
        ["xdotool", "type", "--clearmodifiers", "--delay", "12", "--", text],
        check=True,
        capture_output=True,
        text=True,
    )


def _type_ydotool(text: str) -> None:
    subprocess.run(
        ["ydotool", "type", "--", text],
        check=True,
        capture_output=True,
        text=True,
    )


def _type_wtype(text: str) -> None:
    subprocess.run(
        ["wtype", "--", text],
        check=True,
        capture_output=True,
        text=True,
    )


def _key_xdotool(key: str) -> None:
    subprocess.run(
        ["xdotool", "key", "--clearmodifiers", key],
        check=True,
        capture_output=True,
        text=True,
    )


def _key_ydotool(key: str) -> None:
    # ydotool uses key codes; map a few common ones.
    mapping = {"Tab": "15:1 15:0", "Return": "28:1 28:0", "enter": "28:1 28:0"}
    seq = mapping.get(key, "")
    if not seq:
        raise AutoTypeError(f"ydotool key not mapped: {key}")
    subprocess.run(
        ["ydotool", "key", *seq.split()],
        check=True,
        capture_output=True,
        text=True,
    )


def _key_wtype(key: str) -> None:
    mapping = {"Tab": "Tab", "Return": "Return", "enter": "Return"}
    name = mapping.get(key, key)
    subprocess.run(
        ["wtype", "-k", name],
        check=True,
        capture_output=True,
        text=True,
    )


def expand_sequence(
    sequence: str,
    *,
    username: str,
    password: str,
    totp: str = "",
    url: str = "",
) -> list[tuple[str, str]]:
    """Expand KeePass-like tokens into (op, value) steps: type|key|delay."""
    tokens = {
        "{USERNAME}": ("type", username),
        "{PASSWORD}": ("type", password),
        "{TOTP}": ("type", totp),
        "{URL}": ("type", url),
        "{TAB}": ("key", "Tab"),
        "{ENTER}": ("key", "Return"),
        "{DELAY}": ("delay", "250"),
    }
    steps: list[tuple[str, str]] = []
    i = 0
    buf: list[str] = []
    upper = sequence
    while i < len(upper):
        if upper[i] == "{":
            end = upper.find("}", i)
            if end == -1:
                buf.append(upper[i:])
                break
            token = upper[i : end + 1].upper()
            # Preserve original-case token lookup for known set.
            matched = None
            for key, step in tokens.items():
                if token == key:
                    matched = step
                    break
            if matched is not None:
                if buf:
                    steps.append(("type", "".join(buf)))
                    buf.clear()
                steps.append(matched)
            else:
                buf.append(upper[i : end + 1])
            i = end + 1
            continue
        buf.append(upper[i])
        i += 1
    if buf:
        steps.append(("type", "".join(buf)))
    return steps


def auto_type(
    sequence: str,
    *,
    username: str,
    password: str,
    totp: str = "",
    url: str = "",
    initial_delay_ms: int = 1500,
) -> str:
    """Perform Auto-Type. Returns backend name used."""
    backend = detect_backend()
    if backend is None:
        raise AutoTypeError(
            "No Auto-Type backend found. Install xdotool (X11), "
            "ydotool, or wtype (Wayland)."
        )
    time.sleep(max(0, initial_delay_ms) / 1000.0)
    steps = expand_sequence(
        sequence, username=username, password=password, totp=totp, url=url
    )
    try:
        for op, value in steps:
            if op == "delay":
                time.sleep(int(value) / 1000.0)
                continue
            if op == "type":
                if not value:
                    continue
                if backend == "xdotool":
                    _type_xdotool(value)
                elif backend == "ydotool":
                    _type_ydotool(value)
                else:
                    _type_wtype(value)
                continue
            if op == "key":
                if backend == "xdotool":
                    _key_xdotool(value)
                elif backend == "ydotool":
                    _key_ydotool(value)
                else:
                    _key_wtype(value)
    except subprocess.CalledProcessError as exc:
        raise AutoTypeError(
            f"Auto-Type backend '{backend}' failed "
            f"(exit {exc.returncode}). Secrets were not included in this message."
        ) from None
    except OSError as exc:
        raise AutoTypeError(f"Auto-Type backend error: {exc}") from None
    return backend
