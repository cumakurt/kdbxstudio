"""Password audit engine for the Password Health Dashboard."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from kdbxstudio.application.database_manager import DatabaseManager
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

    @property
    def severity_counts(self) -> dict[str, int]:
        counts = Counter(f.severity for f in self.findings)
        return {
            "critical": int(counts.get("critical", 0)),
            "warning": int(counts.get("warning", 0)),
            "info": int(counts.get("info", 0)),
        }


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

    def __init__(self, database_manager: DatabaseManager) -> None:
        self._dbm = database_manager

    def run(
        self,
        session_id: str | None = None,
        *,
        include_recycle_bin: bool = False,
    ) -> AuditReport:
        entries = self._dbm.all_entries(
            session_id, include_recycle_bin=include_recycle_bin
        )
        findings: list[AuditFinding] = []
        empty = 0
        weak = 0
        low_entropy = 0
        missing_usernames = 0

        password_map: dict[str, list[EntryView]] = {}
        username_map: dict[str, list[EntryView]] = {}

        for entry in entries:
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
        )
