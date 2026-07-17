"""Tests for password generator and recent database list."""

from pathlib import Path

from kdbxstudio.core.password_generator import (
    GeneratorOptions,
    build_alphabet,
    generate_password,
)
from kdbxstudio.security.store import (
    clear_recent_databases,
    load_recent_databases,
    remember_database,
)


def test_generate_password_length_and_classes() -> None:
    opts = GeneratorOptions(length=24, symbols=True, exclude_ambiguous=True)
    password = generate_password(opts)
    assert len(password) == 24
    alphabet = build_alphabet(opts)
    assert all(ch in alphabet for ch in password)
    assert "0" not in password
    assert "O" not in password


def test_generate_password_requires_alphabet() -> None:
    try:
        generate_password(
            GeneratorOptions(
                uppercase=False,
                lowercase=False,
                digits=False,
                symbols=False,
            )
        )
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_recent_databases(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    a = tmp_path / "a.kdbx"
    b = tmp_path / "b.kdbx"
    a.write_text("x")
    b.write_text("y")
    remember_database(a, settings)
    remember_database(b, settings)
    remember_database(a, settings)
    recent = load_recent_databases(settings)
    assert recent[0].resolve() == a.resolve()
    assert recent[1].resolve() == b.resolve()
    clear_recent_databases(settings)
    assert load_recent_databases(settings) == []
