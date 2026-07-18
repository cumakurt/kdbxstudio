"""Frozen DTOs for the Security Dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field

from kdbxstudio.application.audit_engine import AuditFinding, AuditReport


@dataclass(frozen=True)
class NamedCount:
    name: str
    count: int


@dataclass(frozen=True)
class DuplicateGroup:
    entry_count: int
    titles: tuple[str, ...]
    entry_uuids: tuple[str, ...]


@dataclass(frozen=True)
class EntryRef:
    uuid: str
    title: str
    detail: str = ""


@dataclass(frozen=True)
class DashboardSnapshot:
    """Complete analytics payload for the Security Dashboard UI."""

    audit: AuditReport
    security_score: int
    score_label: str
    recommendations: tuple[str, ...]

    # Password statistics (strength buckets)
    strength_strong: int = 0
    strength_good: int = 0
    strength_fair: int = 0
    strength_weak: int = 0
    strength_very_weak: int = 0
    strength_empty: int = 0

    # Duplicates
    duplicate_password_groups: int = 0
    duplicate_total_reuses: int = 0
    most_reused_password_count: int = 0
    duplicate_groups: tuple[DuplicateGroup, ...] = ()

    # Password age (mtime days)
    age_0_30: int = 0
    age_30_90: int = 0
    age_90_180: int = 0
    age_180_365: int = 0
    age_365_plus: int = 0
    age_unknown: int = 0

    # Expiry buckets
    expired_count: int = 0
    expiring_7: int = 0
    expiring_30: int = 0
    expiring_90: int = 0

    # Entropy
    entropy_avg: float = 0.0
    entropy_min: float = 0.0
    entropy_max: float = 0.0
    entropy_buckets: tuple[NamedCount, ...] = ()

    # Length
    length_under_8: int = 0
    length_8: int = 0
    length_12: int = 0
    length_16: int = 0
    length_20_plus: int = 0

    # Categories
    categories: tuple[NamedCount, ...] = ()

    # OTP
    otp_with: int = 0
    otp_without: int = 0
    otp_critical_missing: int = 0

    # Tags
    top_tags: tuple[NamedCount, ...] = ()
    untagged: int = 0

    # Username
    empty_usernames: int = 0
    reused_usernames: int = 0
    admin_usernames: int = 0
    root_usernames: int = 0

    # URL
    url_empty: int = 0
    url_https: int = 0
    url_http: int = 0
    url_other: int = 0

    # Certificates
    cert_total: int = 0
    cert_expired: int = 0
    cert_expiring_soon: int = 0
    cert_entries: tuple[EntryRef, ...] = ()

    # SSH
    ssh_rsa: int = 0
    ssh_ed25519: int = 0
    ssh_ecdsa: int = 0
    ssh_other: int = 0
    ssh_encrypted: int = 0
    ssh_total: int = 0

    # Attachments
    attachment_types: tuple[NamedCount, ...] = ()
    attachment_size_buckets: tuple[NamedCount, ...] = ()
    attachment_total: int = 0
    attachment_total_bytes: int = 0

    # Favorites / recent
    favorite_entries: tuple[EntryRef, ...] = ()
    recently_accessed: tuple[EntryRef, ...] = ()
    recently_modified: tuple[EntryRef, ...] = ()

    # Database health
    total_groups: int = 0
    total_entries: int = 0
    total_attachments: int = 0
    total_otp: int = 0
    total_certificates: int = 0
    total_ssh_keys: int = 0

    # Risk matrix
    risk_critical: int = 0
    risk_high: int = 0
    risk_medium: int = 0
    risk_low: int = 0

    findings: tuple[AuditFinding, ...] = field(default_factory=tuple)

    @property
    def total_passwords(self) -> int:
        return self.total_entries
