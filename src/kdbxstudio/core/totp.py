"""TOTP helpers built on pyotp."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import pyotp


@dataclass(frozen=True)
class TotpStatus:
    code: str
    remaining_seconds: int
    period: int
    label: str
    valid: bool
    error: str = ""


def parse_otp_uri_or_secret(value: str) -> tuple[pyotp.TOTP | None, str]:
    """Return (totp, label) from an otpauth URI or bare base32 secret."""
    text = (value or "").strip()
    if not text:
        return None, ""
    if text.lower().startswith("otpauth://"):
        totp = pyotp.parse_uri(text)
        if not isinstance(totp, pyotp.TOTP):
            return None, ""
        parsed = urlparse(text)
        label = parsed.path.lstrip("/")
        return totp, label
    # bare secret
    try:
        totp = pyotp.TOTP(text.replace(" ", "").upper())
        # Validate by generating once
        _ = totp.now()
        return totp, "TOTP"
    except Exception:
        return None, ""


def current_totp(value: str) -> TotpStatus:
    try:
        totp, label = parse_otp_uri_or_secret(value)
        if totp is None:
            return TotpStatus(
                code="",
                remaining_seconds=0,
                period=30,
                label="",
                valid=False,
                error="No valid TOTP configuration",
            )
        period = int(getattr(totp, "interval", 30) or 30)
        import time

        remaining = period - (int(time.time()) % period)
        return TotpStatus(
            code=totp.now(),
            remaining_seconds=remaining,
            period=period,
            label=label,
            valid=True,
        )
    except Exception as exc:
        return TotpStatus(
            code="",
            remaining_seconds=0,
            period=30,
            label="",
            valid=False,
            error=str(exc),
        )


def looks_like_otp(value: str) -> bool:
    text = (value or "").strip().lower()
    return text.startswith("otpauth://") or (
        len(text.replace(" ", "")) >= 16
        and all(c in "abcdefghijklmnopqrstuvwxyz234567=" for c in text.replace(" ", ""))
    )
