"""Cryptographically strong password generator."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratorOptions:
    length: int = 20
    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = True


_AMBIGUOUS = set("O0Il1|`\"'")


def build_alphabet(options: GeneratorOptions) -> str:
    chars = ""
    if options.lowercase:
        chars += string.ascii_lowercase
    if options.uppercase:
        chars += string.ascii_uppercase
    if options.digits:
        chars += string.digits
    if options.symbols:
        chars += "!@#$%^&*()-_=+[]{};:,.<>?/\\~"
    if options.exclude_ambiguous:
        chars = "".join(c for c in chars if c not in _AMBIGUOUS)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for c in chars:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return "".join(unique)


def generate_password(options: GeneratorOptions | None = None) -> str:
    opts = options or GeneratorOptions()
    if opts.length < 4:
        raise ValueError("Password length must be at least 4")
    alphabet = build_alphabet(opts)
    if not alphabet:
        raise ValueError("Alphabet is empty; enable at least one character class")

    # Guarantee one char from each enabled class when possible
    required: list[str] = []
    classes: list[str] = []
    if opts.lowercase:
        classes.append(
            "".join(
                c
                for c in string.ascii_lowercase
                if not opts.exclude_ambiguous or c not in _AMBIGUOUS
            )
        )
    if opts.uppercase:
        classes.append(
            "".join(
                c
                for c in string.ascii_uppercase
                if not opts.exclude_ambiguous or c not in _AMBIGUOUS
            )
        )
    if opts.digits:
        classes.append(
            "".join(
                c
                for c in string.digits
                if not opts.exclude_ambiguous or c not in _AMBIGUOUS
            )
        )
    if opts.symbols:
        sym = "!@#$%^&*()-_=+[]{};:,.<>?/\\~"
        classes.append(
            "".join(
                c for c in sym if not opts.exclude_ambiguous or c not in _AMBIGUOUS
            )
        )
    for class_chars in classes:
        if class_chars:
            required.append(secrets.choice(class_chars))

    remaining = opts.length - len(required)
    if remaining < 0:
        # Truncate required set if length is smaller than class count
        required = required[: opts.length]
        remaining = 0
    body = [secrets.choice(alphabet) for _ in range(remaining)]
    chars = required + body
    # Fisher–Yates with secrets
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def estimate_entropy_bits(password: str, alphabet_size: int) -> float:
    if not password or alphabet_size <= 1:
        return 0.0
    # length * log2(alphabet)
    import math

    return len(password) * math.log2(alphabet_size)
