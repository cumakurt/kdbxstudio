"""Tests for secure memory helpers."""

from kdbxstudio.core.crypto import SecureString, wipe_bytearray


def test_wipe_bytearray() -> None:
    buf = bytearray(b"secret")
    wipe_bytearray(buf)
    assert buf == bytearray(b"\x00" * 6)


def test_secure_string_roundtrip() -> None:
    s = SecureString("hunter2")
    assert s.get() == "hunter2"
    assert len(s) == 7
    s.wipe()
    assert s.get() == ""
    assert not s
