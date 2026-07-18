"""Weighted Security Score for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreInputs:
    total_entries: int
    empty_passwords: int = 0
    very_weak: int = 0
    weak: int = 0
    fair: int = 0
    duplicates: int = 0
    expired: int = 0
    expiring_7: int = 0
    expiring_30: int = 0
    expiring_90: int = 0
    age_365_plus: int = 0
    empty_usernames: int = 0
    empty_urls: int = 0
    otp_critical_missing: int = 0
    short_passwords: int = 0
    low_entropy: int = 0
    pwned: int = 0
    cert_expired: int = 0
    cert_expiring_soon: int = 0


def score_label(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 50:
        return "Needs Attention"
    return "Critical"


def compute_security_score(inputs: ScoreInputs) -> tuple[int, str]:
    """Return (0-100 score, English label). Penalties scale with issue density."""
    if inputs.total_entries <= 0:
        return 100, score_label(100)

    n = float(inputs.total_entries)
    penalty = 0.0

    def dens(count: int) -> float:
        return min(1.0, count / n)

    penalty += dens(inputs.empty_passwords) * 25
    penalty += dens(inputs.very_weak) * 18
    penalty += dens(inputs.weak) * 12
    penalty += dens(inputs.fair) * 4
    penalty += dens(inputs.duplicates) * 15
    penalty += dens(inputs.expired) * 12
    penalty += dens(inputs.expiring_7) * 8
    penalty += dens(inputs.expiring_30) * 5
    penalty += dens(inputs.expiring_90) * 2
    penalty += dens(inputs.age_365_plus) * 8
    penalty += dens(inputs.empty_usernames) * 3
    penalty += dens(inputs.empty_urls) * 2
    penalty += dens(inputs.otp_critical_missing) * 10
    penalty += dens(inputs.short_passwords) * 10
    penalty += dens(inputs.low_entropy) * 8
    penalty += dens(inputs.pwned) * 20
    penalty += dens(inputs.cert_expired) * 6
    penalty += dens(inputs.cert_expiring_soon) * 3

    score = max(0, min(100, int(round(100 - penalty))))
    return score, score_label(score)
