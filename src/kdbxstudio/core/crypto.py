"""Secure memory helpers for sensitive strings."""

from __future__ import annotations

import secrets
from collections.abc import MutableSequence


def wipe_bytearray(buf: MutableSequence[int]) -> None:
    """Overwrite a mutable byte buffer with random data, then zeros."""
    length = len(buf)
    if length == 0:
        return
    random_bytes = secrets.token_bytes(length)
    for i, value in enumerate(random_bytes):
        buf[i] = value
    for i in range(length):
        buf[i] = 0


def wipe_bytes(data: bytearray | memoryview[int]) -> None:
    """Wipe a bytearray or writable memoryview in place."""
    if isinstance(data, memoryview):
        if data.readonly:
            raise ValueError("Cannot wipe a read-only memoryview")
        for i in range(len(data)):
            data[i] = secrets.randbelow(256)
        for i in range(len(data)):
            data[i] = 0
        return
    wipe_bytearray(data)


class SecureString:
    """Mutable string stored as a bytearray that can be wiped.

    This is a best-effort helper; Python strings and GC copies may still
    linger. Prefer short lifetimes for secrets and wipe when done.
    """

    __slots__ = ("_data",)

    def __init__(self, value: str = "") -> None:
        self._data = bytearray(value.encode("utf-8"))

    def set(self, value: str) -> None:
        wipe_bytearray(self._data)
        self._data = bytearray(value.encode("utf-8"))

    def get(self) -> str:
        return self._data.decode("utf-8")

    def wipe(self) -> None:
        wipe_bytearray(self._data)
        self._data = bytearray()

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)

    def __del__(self) -> None:
        try:
            self.wipe()
        except Exception:
            pass
