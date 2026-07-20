"""Human-readable recommendations from a dashboard snapshot."""

from __future__ import annotations

from kdbxstudio.application.security_dashboard.models import DashboardSnapshot


def build_recommendations(snapshot: DashboardSnapshot) -> tuple[str, ...]:
    lines: list[str] = []
    weakish = (
        snapshot.strength_weak + snapshot.strength_very_weak + snapshot.strength_empty
    )
    if weakish:
        lines.append(f"{weakish} weak or empty password(s) should be replaced.")
    if snapshot.duplicate_total_reuses:
        lines.append(
            f"{snapshot.duplicate_password_groups} password(s) are reused "
            f"across {snapshot.duplicate_total_reuses} entries."
        )
    if snapshot.age_365_plus:
        lines.append(
            f"{snapshot.age_365_plus} password(s) have not been changed in over a year."
        )
    if snapshot.expired_count:
        lines.append(f"{snapshot.expired_count} entry expiry date(s) have passed.")
    if snapshot.expiring_7:
        lines.append(f"{snapshot.expiring_7} entry/entries expire within 7 days.")
    if snapshot.cert_expiring_soon:
        lines.append(f"{snapshot.cert_expiring_soon} certificate(s) expire soon.")
    if snapshot.cert_expired:
        lines.append(f"{snapshot.cert_expired} certificate(s) have expired.")
    if snapshot.otp_critical_missing:
        lines.append(
            f"{snapshot.otp_critical_missing} critical entr"
            f"{'y' if snapshot.otp_critical_missing == 1 else 'ies'} "
            "have no OTP."
        )
    if snapshot.empty_usernames:
        lines.append(
            f"{snapshot.empty_usernames} entr"
            f"{'y has' if snapshot.empty_usernames == 1 else 'ies have'} "
            "an empty username."
        )
    if snapshot.url_http:
        lines.append(f"{snapshot.url_http} URL(s) use HTTP instead of HTTPS.")
    if snapshot.audit.pwned:
        lines.append(f"{snapshot.audit.pwned} password(s) appear in known breaches.")
    if snapshot.ssh_total and snapshot.ssh_encrypted < snapshot.ssh_total:
        unenc = snapshot.ssh_total - snapshot.ssh_encrypted
        lines.append(f"{unenc} SSH key(s) are not passphrase-protected.")
    if not lines:
        lines.append(
            "No critical issues detected. Keep rotating credentials regularly."
        )
    return tuple(lines)
