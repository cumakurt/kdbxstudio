"""Password audit engine for the Password Health Dashboard."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.expiry import parse_expiry
from kdbxstudio.core.database import EntryView
from kdbxstudio.core.password_generator import estimate_entropy_bits


@dataclass(frozen=True)
class AuditFinding:
    kind: str
    message: str
    entry_uuid: str | None
    severity: str  # info | warning | critical


@dataclass(frozen=True)
class AuditReport:
    findings: tuple[AuditFinding, ...]
    total_entries: int
    empty_passwords: int
    duplicates: int
    weak_passwords: int
    low_entropy: int = 0
    missing_usernames: int = 0
    reused_usernames: int = 0
    expired: int = 0
    expiring_soon: int = 0
    pwned: int = 0
    total_groups: int = 0
    entries_with_attachments: int = 0
    entries_with_otp: int = 0
    entries_with_url: int = 0
    entries_with_tags: int = 0
    entries_with_custom_fields: int = 0

    @property
    def severity_counts(self) -> dict[str, int]:
        counts = Counter(f.severity for f in self.findings)
        return {
            "critical": int(counts.get("critical", 0)),
            "warning": int(counts.get("warning", 0)),
            "info": int(counts.get("info", 0)),
        }

    @property
    def health_score(self) -> int:
        if self.total_entries == 0:
            return 100
        good = self.total_entries - self.empty_passwords - self.weak_passwords
        good = max(0, good)
        return min(100, int(good * 100 / self.total_entries))


def _charset_size(password: str) -> int:
    size = 0
    if any(c.islower() for c in password):
        size += 26
    if any(c.isupper() for c in password):
        size += 26
    if any(c.isdigit() for c in password):
        size += 10
    if any(not c.isalnum() for c in password):
        size += 32
    return max(size, 1)


def password_entropy_bits(password: str) -> float:
    return estimate_entropy_bits(password, _charset_size(password))


class AuditEngine:
    """Password health checks for empty, weak, duplicate, and entropy issues."""

    WEAK_LENGTH = 8
    LOW_ENTROPY_BITS = 40.0
    REUSED_USERNAME_THRESHOLD = 3
    EXPIRING_SOON_DAYS = 14

    def __init__(self, database_manager: DatabaseManager) -> None:
        self._dbm = database_manager

    def run(
        self,
        session_id: str | None = None,
        *,
        include_recycle_bin: bool = False,
        check_hibp: bool = False,
        hibp_limit: int = 40,
    ) -> AuditReport:
        entries = self._dbm.all_entries(
            session_id, include_recycle_bin=include_recycle_bin
        )
        findings: list[AuditFinding] = []
        empty = 0
        weak = 0
        low_entropy = 0
        missing_usernames = 0
        expired = 0
        expiring_soon = 0
        pwned = 0
        with_attachments = 0
        with_otp = 0
        with_url = 0
        with_tags = 0
        with_custom = 0

        password_map: dict[str, list[EntryView]] = {}
        username_map: dict[str, list[EntryView]] = {}
        now = datetime.now(UTC)
        soon = now + timedelta(days=self.EXPIRING_SOON_DAYS)

        try:
            group_count = len(self._dbm.list_groups())
        except Exception:
            group_count = 0

        for entry in entries:
            if (entry.url or "").strip():
                with_url += 1
            if entry.tags:
                with_tags += 1
            if entry.custom_properties:
                with_custom += 1
            if entry.otp:
                with_otp += 1
            try:
                if self._dbm.attachment_count(entry.uuid) > 0:
                    with_attachments += 1
            except Exception:
                pass
            username = (entry.username or "").strip()
            if not username:
                missing_usernames += 1
                findings.append(
                    AuditFinding(
                        kind="missing_username",
                        message=f"Entry '{entry.title}' has no username",
                        entry_uuid=entry.uuid,
                        severity="info",
                    )
                )
            else:
                username_map.setdefault(username.lower(), []).append(entry)

            expiry = parse_expiry(entry)
            if expiry is not None:
                if expiry <= now:
                    expired += 1
                    findings.append(
                        AuditFinding(
                            kind="expired",
                            message=f"Entry '{entry.title}' expired on {expiry.date()}",
                            entry_uuid=entry.uuid,
                            severity="critical",
                        )
                    )
                elif expiry <= soon:
                    expiring_soon += 1
                    findings.append(
                        AuditFinding(
                            kind="expiring_soon",
                            message=(
                                f"Entry '{entry.title}' expires on {expiry.date()}"
                            ),
                            entry_uuid=entry.uuid,
                            severity="warning",
                        )
                    )

            pwd = entry.password or ""
            if not pwd:
                empty += 1
                findings.append(
                    AuditFinding(
                        kind="empty_password",
                        message=f"Entry '{entry.title}' has an empty password",
                        entry_uuid=entry.uuid,
                        severity="critical",
                    )
                )
                continue
            password_map.setdefault(pwd, []).append(entry)
            if len(pwd) < self.WEAK_LENGTH:
                weak += 1
                findings.append(
                    AuditFinding(
                        kind="weak_password",
                        message=(
                            f"Entry '{entry.title}' password is shorter than "
                            f"{self.WEAK_LENGTH} characters"
                        ),
                        entry_uuid=entry.uuid,
                        severity="warning",
                    )
                )
            else:
                bits = password_entropy_bits(pwd)
                if bits < self.LOW_ENTROPY_BITS:
                    low_entropy += 1
                    findings.append(
                        AuditFinding(
                            kind="low_entropy",
                            message=(
                                f"Entry '{entry.title}' password has low "
                                f"estimated entropy ({bits:.0f} bits)"
                            ),
                            entry_uuid=entry.uuid,
                            severity="warning",
                        )
                    )

        if check_hibp:
            from kdbxstudio.application.hibp import HibpError, pwned_count

            checked = 0
            seen_pw: dict[str, int] = {}
            for entry in entries:
                if checked >= hibp_limit:
                    findings.append(
                        AuditFinding(
                            kind="hibp_truncated",
                            message=(
                                f"HIBP check limited to {hibp_limit} passwords "
                                "this run"
                            ),
                            entry_uuid=None,
                            severity="info",
                        )
                    )
                    break
                pwd = entry.password or ""
                if not pwd:
                    continue
                try:
                    if pwd in seen_pw:
                        count = seen_pw[pwd]
                    else:
                        count = pwned_count(pwd)
                        seen_pw[pwd] = count
                        checked += 1
                except HibpError as exc:
                    findings.append(
                        AuditFinding(
                            kind="hibp_error",
                            message=str(exc),
                            entry_uuid=None,
                            severity="info",
                        )
                    )
                    break
                if count > 0:
                    pwned += 1
                    findings.append(
                        AuditFinding(
                            kind="pwned_password",
                            message=(
                                f"Entry '{entry.title}' password seen in breaches "
                                f"({count} times)"
                            ),
                            entry_uuid=entry.uuid,
                            severity="critical",
                        )
                    )

        duplicates = 0
        for _pwd, group in password_map.items():
            if len(group) < 2:
                continue
            duplicates += len(group)
            titles = ", ".join(e.title for e in group)
            findings.append(
                AuditFinding(
                    kind="duplicate_password",
                    message=f"Duplicate password used by: {titles}",
                    entry_uuid=group[0].uuid,
                    severity="warning",
                )
            )

        reused_usernames = 0
        for username, group in username_map.items():
            if len(group) < self.REUSED_USERNAME_THRESHOLD:
                continue
            reused_usernames += len(group)
            titles = ", ".join(e.title for e in group[:5])
            extra = "" if len(group) <= 5 else f" (+{len(group) - 5} more)"
            findings.append(
                AuditFinding(
                    kind="reused_username",
                    message=(
                        f"Username '{username}' reused across "
                        f"{len(group)} entries: {titles}{extra}"
                    ),
                    entry_uuid=group[0].uuid,
                    severity="info",
                )
            )

        return AuditReport(
            findings=tuple(findings),
            total_entries=len(entries),
            empty_passwords=empty,
            duplicates=duplicates,
            weak_passwords=weak,
            low_entropy=low_entropy,
            missing_usernames=missing_usernames,
            reused_usernames=reused_usernames,
            expired=expired,
            expiring_soon=expiring_soon,
            pwned=pwned,
            total_groups=group_count,
            entries_with_attachments=with_attachments,
            entries_with_otp=with_otp,
            entries_with_url=with_url,
            entries_with_tags=with_tags,
            entries_with_custom_fields=with_custom,
        )
