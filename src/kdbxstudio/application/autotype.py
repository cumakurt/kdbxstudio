"""Linux Auto-Type helper (xdotool / ydotool / wtype)."""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from dataclasses import dataclass

from kdbxstudio.core.database import EntryView


class AutoTypeError(Exception):
    """Raised when no suitable typer backend is available."""


_DELAY_RE = re.compile(r"^\{DELAY(?:=(\d+))?\}$", re.IGNORECASE)
_COMMAND_TIMEOUT_S = 10


@dataclass(frozen=True)
class WindowMatch:
    entry: EntryView
    score: int
    reason: str


def detect_backend() -> str | None:
    for name in ("xdotool", "ydotool", "wtype"):
        if shutil.which(name):
            return name
    return None


def active_window_title() -> str | None:
    """Best-effort foreground window title (X11 via xdotool; optional Wayland tools)."""
    if shutil.which("xdotool"):
        try:
            proc = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True,
                text=True,
                check=False,
                timeout=2,
            )
            title = (proc.stdout or "").strip()
            if title:
                return title
        except (OSError, subprocess.TimeoutExpired):
            pass
    # Hyprland
    if shutil.which("hyprctl"):
        try:
            proc = subprocess.run(
                ["hyprctl", "activewindow", "-j"],
                capture_output=True,
                text=True,
                check=False,
                timeout=2,
            )
            if proc.returncode == 0 and '"title"' in (proc.stdout or ""):
                import json

                data = json.loads(proc.stdout)
                title = str(data.get("title") or "").strip()
                if title:
                    return title
        except (OSError, subprocess.TimeoutExpired, ValueError, TypeError):
            pass
    return None


def score_entry_for_window(entry: EntryView, window_title: str) -> WindowMatch | None:
    """Score how well an entry matches a window title / URL host."""
    title = (window_title or "").strip().lower()
    if not title:
        return None
    best = 0
    reason = ""
    entry_title = (entry.title or "").strip().lower()
    if entry_title and entry_title in title:
        best = max(best, 80 + min(len(entry_title), 20))
        reason = "title-in-window"
    elif entry_title and title in entry_title:
        best = max(best, 60)
        reason = "window-in-title"
    url = (entry.url or "").strip().lower()
    if url:
        host = url
        for prefix in ("https://", "http://"):
            if host.startswith(prefix):
                host = host[len(prefix) :]
        host = host.split("/", 1)[0]
        if host.startswith("www."):
            host = host[4:]
        if host and host in title:
            if 70 > best:
                best = 70
                reason = "url-host-in-window"
        # Compare first label (example.com → example)
        label = host.split(".", 1)[0] if host else ""
        if label and len(label) >= 3 and label in title and best < 55:
            best = 55
            reason = "url-label-in-window"
    if best <= 0:
        return None
    return WindowMatch(entry=entry, score=best, reason=reason)


def find_best_entry_for_window(
    entries: list[EntryView],
    window_title: str | None = None,
) -> WindowMatch | None:
    """Pick the highest-scoring non-recycle entry for the active window."""
    title = window_title if window_title is not None else active_window_title()
    if not title:
        return None
    best: WindowMatch | None = None
    for entry in entries:
        if entry.in_recycle_bin:
            continue
        match = score_entry_for_window(entry, title)
        if match is None:
            continue
        if best is None or match.score > best.score:
            best = match
    return best


def _type_xdotool(text: str) -> None:
    subprocess.run(
        ["xdotool", "type", "--clearmodifiers", "--delay", "12", "--file", "-"],
        input=text,
        check=True,
        capture_output=True,
        text=True,
        timeout=_COMMAND_TIMEOUT_S,
    )


def _type_ydotool(text: str) -> None:
    subprocess.run(
        ["ydotool", "stdin"],
        input=text,
        check=True,
        capture_output=True,
        text=True,
        timeout=_COMMAND_TIMEOUT_S,
    )


def _type_wtype(text: str) -> None:
    subprocess.run(
        ["wtype", "-"],
        input=text,
        check=True,
        capture_output=True,
        text=True,
        timeout=_COMMAND_TIMEOUT_S,
    )


def _key_xdotool(key: str) -> None:
    subprocess.run(
        ["xdotool", "key", "--clearmodifiers", key],
        check=True,
        capture_output=True,
        text=True,
        timeout=_COMMAND_TIMEOUT_S,
    )


def _key_ydotool(key: str) -> None:
    mapping = {"Tab": "15:1 15:0", "Return": "28:1 28:0", "enter": "28:1 28:0"}
    seq = mapping.get(key, "")
    if not seq:
        raise AutoTypeError(f"ydotool key not mapped: {key}")
    subprocess.run(
        ["ydotool", "key", *seq.split()],
        check=True,
        capture_output=True,
        text=True,
        timeout=_COMMAND_TIMEOUT_S,
    )


def _key_wtype(key: str) -> None:
    mapping = {"Tab": "Tab", "Return": "Return", "enter": "Return"}
    name = mapping.get(key, key)
    subprocess.run(
        ["wtype", "-k", name],
        check=True,
        capture_output=True,
        text=True,
        timeout=_COMMAND_TIMEOUT_S,
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
    while i < len(sequence):
        if sequence[i] == "{":
            end = sequence.find("}", i)
            if end == -1:
                buf.append(sequence[i:])
                break
            raw_token = sequence[i : end + 1]
            token = raw_token.upper()
            delay_match = _DELAY_RE.match(raw_token)
            if delay_match is not None:
                if buf:
                    steps.append(("type", "".join(buf)))
                    buf.clear()
                raw_ms = (delay_match.group(1) or "250").lstrip("0") or "0"
                ms = "60000" if len(raw_ms) > 5 else str(min(60_000, int(raw_ms)))
                steps.append(("delay", ms))
                i = end + 1
                continue
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
                buf.append(raw_token)
            i = end + 1
            continue
        buf.append(sequence[i])
        i += 1
    if buf:
        steps.append(("type", "".join(buf)))
    return steps


def run_autotype_steps(
    steps: list[tuple[str, str]],
    *,
    backend: str | None = None,
) -> str:
    """Execute expanded Auto-Type steps. Returns backend name used."""
    chosen = backend or detect_backend()
    if chosen is None:
        raise AutoTypeError(
            "No Auto-Type backend found. Install xdotool (X11), "
            "ydotool, or wtype (Wayland)."
        )
    if chosen not in {"xdotool", "ydotool", "wtype"}:
        raise AutoTypeError(f"Unsupported Auto-Type backend: {chosen}")
    try:
        for op, value in steps:
            if op == "delay":
                time.sleep(min(60_000, max(0, int(value))) / 1000.0)
                continue
            if op == "type":
                if not value:
                    continue
                if chosen == "xdotool":
                    _type_xdotool(value)
                elif chosen == "ydotool":
                    _type_ydotool(value)
                else:
                    _type_wtype(value)
                continue
            if op == "key":
                if chosen == "xdotool":
                    _key_xdotool(value)
                elif chosen == "ydotool":
                    _key_ydotool(value)
                else:
                    _key_wtype(value)
    except subprocess.CalledProcessError as exc:
        raise AutoTypeError(
            f"Auto-Type backend '{chosen}' failed "
            f"(exit {exc.returncode}). Secrets were not included in this message."
        ) from None
    except subprocess.TimeoutExpired:
        raise AutoTypeError(
            f"Auto-Type backend '{chosen}' timed out. Secrets were not logged."
        ) from None
    except OSError as exc:
        raise AutoTypeError(f"Auto-Type backend error: {exc}") from None
    return chosen


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
    if initial_delay_ms > 0:
        time.sleep(min(initial_delay_ms, 60_000) / 1000.0)
    steps = expand_sequence(
        sequence, username=username, password=password, totp=totp, url=url
    )
    return run_autotype_steps(steps)
