"""Password strength scoring shared by entry detail and Security Dashboard."""

from __future__ import annotations

import math
import re
from enum import StrEnum


class StrengthBucket(StrEnum):
    EMPTY = "empty"
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    FAIR = "fair"
    GOOD = "good"
    STRONG = "strong"


def estimate_password_strength(password: str) -> tuple[int, StrengthBucket]:
    """Return (score 0-100, bucket) for a password. Labels are caller-localized."""
    if not password:
        return 0, StrengthBucket.EMPTY
    score = 0
    length = len(password)
    if length >= 8:
        score += 20
    elif length >= 6:
        score += 10
    if length >= 16:
        score += 20
    elif length >= 12:
        score += 15
    if re.search(r"[a-z]", password):
        score += 10
    if re.search(r"[A-Z]", password):
        score += 10
    if re.search(r"\d", password):
        score += 10
    if re.search(r"[^a-zA-Z0-9]", password):
        score += 15
    unique_chars = len(set(password))
    if unique_chars >= 10:
        score += 10
    elif unique_chars >= 6:
        score += 5
    entropy = len(password) * math.log2(max(1, unique_chars))
    if entropy >= 60:
        score += 10
    elif entropy >= 40:
        score += 5
    score = min(100, score)
    if score >= 80:
        return score, StrengthBucket.STRONG
    if score >= 60:
        return score, StrengthBucket.GOOD
    if score >= 40:
        return score, StrengthBucket.FAIR
    if score >= 20:
        return score, StrengthBucket.WEAK
    return score, StrengthBucket.VERY_WEAK


def strength_tone(score: int) -> str:
    if score >= 60:
        return "success"
    if score >= 20:
        return "warning"
    return "danger"
