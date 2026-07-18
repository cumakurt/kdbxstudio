"""Build a Security Dashboard snapshot from the open database."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from kdbxstudio.application.audit_engine import (
    AuditEngine,
    AuditFinding,
    AuditReport,
    password_entropy_bits,
)
from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.expiry import parse_expiry
from kdbxstudio.application.security_dashboard.categories import (
    DashboardCategory,
    detect_category_from_view,
    is_critical_for_otp,
)
from kdbxstudio.application.security_dashboard.models import (
    DashboardSnapshot,
    DuplicateGroup,
    EntryRef,
    NamedCount,
)
from kdbxstudio.application.security_dashboard.recommendations import (
    build_recommendations,
)
from kdbxstudio.application.security_dashboard.scoring import (
    ScoreInputs,
    compute_security_score,
)
from kdbxstudio.core.database import EntryView
from kdbxstudio.core.password_strength import StrengthBucket, estimate_password_strength
from kdbxstudio.core.pem_inspector import inspect_pem_text

_FAVORITE_TAGS = frozenset({"favorite", "favourite", "★", "star", "fav"})

_ENTROPY_BUCKETS = (
    ("0-30", 0.0, 30.0),
    ("30-40", 30.0, 40.0),
    ("40-60", 40.0, 60.0),
    ("60-80", 60.0, 80.0),
    ("80+", 80.0, 1e9),
)

_SIZE_BUCKETS = (
    ("<10 KB", 0, 10 * 1024),
    ("10-100 KB", 10 * 1024, 100 * 1024),
    ("100 KB-1 MB", 100 * 1024, 1024 * 1024),
    (">1 MB", 1024 * 1024, 1 << 62),
)


def _parse_iso(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except ValueError:
        return None


def _entry_pem_text(entry: EntryView) -> str:
    chunks = [entry.notes, entry.password, entry.username]
    chunks.extend(entry.custom_properties.values())
    return "\n".join(chunks)


def _risk_level(finding: AuditFinding) -> str:
    if finding.severity == "critical":
        return "critical"
    if finding.kind in {
        "duplicate_password",
        "weak_password",
        "low_entropy",
        "expiring_soon",
    }:
        return "high"
    if finding.severity == "warning":
        return "medium"
    return "low"


def _attachment_ext(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower().lstrip(".")
    known = {
        "pdf",
        "pem",
        "zip",
        "json",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "txt",
        "key",
        "crt",
        "cer",
    }
    if suffix in known:
        return suffix.upper() if suffix != "jpeg" else "JPG"
    if not suffix:
        return "Other"
    return suffix.upper()


class SecurityDashboardAnalyzer:
    """Produce a DashboardSnapshot from DatabaseManager + AuditEngine."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self._dbm = database_manager
        self._audit = AuditEngine(database_manager)

    def run(
        self,
        session_id: str | None = None,
        *,
        include_recycle_bin: bool = False,
        check_hibp: bool = False,
        hibp_limit: int = 40,
        audit_report: AuditReport | None = None,
    ) -> DashboardSnapshot:
        report = audit_report or self._audit.run(
            session_id,
            include_recycle_bin=include_recycle_bin,
            check_hibp=check_hibp,
            hibp_limit=hibp_limit,
        )
        entries = self._dbm.all_entries(
            session_id, include_recycle_bin=include_recycle_bin
        )
        return self._analyze(entries, report)

    def _analyze(
        self, entries: list[EntryView], report: AuditReport
    ) -> DashboardSnapshot:
        now = datetime.now(UTC)
        strength = Counter()
        age = Counter()
        length = Counter()
        categories: Counter[str] = Counter()
        tags: Counter[str] = Counter()
        entropy_values: list[float] = []
        entropy_bucket_counts = Counter({label: 0 for label, _, _ in _ENTROPY_BUCKETS})

        password_map: dict[str, list[EntryView]] = {}
        empty_usernames = 0
        admin_usernames = 0
        root_usernames = 0
        username_map: dict[str, list[EntryView]] = {}

        url_empty = url_https = url_http = url_other = 0
        otp_with = otp_without = otp_critical_missing = 0
        untagged = 0

        expired_count = expiring_7 = expiring_30 = expiring_90 = 0
        age_365_plus = 0

        cert_total = cert_expired = cert_expiring_soon = 0
        cert_entries: list[EntryRef] = []
        ssh_rsa = ssh_ed25519 = ssh_ecdsa = ssh_other = ssh_encrypted = ssh_total = 0

        att_types: Counter[str] = Counter()
        att_sizes = Counter({label: 0 for label, _, _ in _SIZE_BUCKETS})
        attachment_total = 0
        attachment_total_bytes = 0

        favorites: list[EntryRef] = []
        access_candidates: list[tuple[datetime, EntryView]] = []
        modified_candidates: list[tuple[datetime, EntryView]] = []

        for entry in entries:
            category = detect_category_from_view(entry)
            categories[category.value] += 1

            pwd = entry.password or ""
            _score, bucket = estimate_password_strength(pwd)
            strength[bucket.value] += 1
            if pwd:
                password_map.setdefault(pwd, []).append(entry)
                bits = password_entropy_bits(pwd)
                entropy_values.append(bits)
                for label, lo, hi in _ENTROPY_BUCKETS:
                    if lo <= bits < hi:
                        entropy_bucket_counts[label] += 1
                        break
                plen = len(pwd)
                if plen < 8:
                    length["under_8"] += 1
                elif plen < 12:
                    length["8"] += 1
                elif plen < 16:
                    length["12"] += 1
                elif plen < 20:
                    length["16"] += 1
                else:
                    length["20_plus"] += 1

            username = (entry.username or "").strip()
            if not username:
                empty_usernames += 1
            else:
                lower = username.lower()
                username_map.setdefault(lower, []).append(entry)
                if lower in {"admin", "administrator"} or lower.endswith("\\admin"):
                    admin_usernames += 1
                if lower == "root":
                    root_usernames += 1

            url = (entry.url or "").strip()
            if not url:
                url_empty += 1
            else:
                parsed = urlparse(url if "://" in url else f"https://{url}")
                scheme = (parsed.scheme or "").lower()
                if scheme == "https":
                    url_https += 1
                elif scheme == "http":
                    url_http += 1
                else:
                    url_other += 1

            if entry.otp:
                otp_with += 1
            else:
                otp_without += 1
                if is_critical_for_otp(category):
                    otp_critical_missing += 1

            if entry.tags:
                for tag in entry.tags:
                    tags[tag] += 1
                    if tag.strip().lower() in _FAVORITE_TAGS:
                        favorites.append(EntryRef(entry.uuid, entry.title, tag))
            else:
                untagged += 1

            mtime = _parse_iso(entry.modified)
            if mtime is None:
                age["unknown"] += 1
            else:
                days = max(0, (now - mtime).days)
                if days <= 30:
                    age["0_30"] += 1
                elif days <= 90:
                    age["30_90"] += 1
                elif days <= 180:
                    age["90_180"] += 1
                elif days <= 365:
                    age["180_365"] += 1
                else:
                    age["365_plus"] += 1
                    age_365_plus += 1
                modified_candidates.append((mtime, entry))

            atime = _parse_iso(entry.accessed)
            if atime is not None:
                access_candidates.append((atime, entry))

            expiry = parse_expiry(entry)
            if expiry is not None:
                if expiry <= now:
                    expired_count += 1
                else:
                    delta = expiry - now
                    if delta <= timedelta(days=7):
                        expiring_7 += 1
                    elif delta <= timedelta(days=30):
                        expiring_30 += 1
                    elif delta <= timedelta(days=90):
                        expiring_90 += 1

            blocks = inspect_pem_text(_entry_pem_text(entry))
            for block in blocks:
                if block.kind == "certificate":
                    cert_total += 1
                    detail = block.not_after or ""
                    cert_entries.append(
                        EntryRef(entry.uuid, entry.title, detail)
                    )
                    na = _parse_iso(block.not_after)
                    if na is not None:
                        if na <= now:
                            cert_expired += 1
                        elif na <= now + timedelta(days=30):
                            cert_expiring_soon += 1
                elif block.kind == "private_key":
                    ssh_total += 1
                    algo = (block.algorithm or "unknown").lower()
                    if algo == "rsa":
                        ssh_rsa += 1
                    elif algo == "ed25519":
                        ssh_ed25519 += 1
                    elif algo == "ecdsa":
                        ssh_ecdsa += 1
                    else:
                        ssh_other += 1
                    if block.encrypted:
                        ssh_encrypted += 1

            if entry.attachment_count > 0:
                try:
                    attachments = self._dbm.list_attachments(entry.uuid)
                except Exception:
                    attachments = []
                for att in attachments:
                    attachment_total += 1
                    attachment_total_bytes += int(att.size or 0)
                    att_types[_attachment_ext(att.filename)] += 1
                    size = int(att.size or 0)
                    for label, lo, hi in _SIZE_BUCKETS:
                        if lo <= size < hi:
                            att_sizes[label] += 1
                            break

        duplicate_groups: list[DuplicateGroup] = []
        duplicate_total = 0
        most_reused = 0
        for _pwd, group in password_map.items():
            if len(group) < 2:
                continue
            duplicate_total += len(group)
            most_reused = max(most_reused, len(group))
            duplicate_groups.append(
                DuplicateGroup(
                    entry_count=len(group),
                    titles=tuple(e.title for e in group[:8]),
                    entry_uuids=tuple(e.uuid for e in group),
                )
            )
        duplicate_groups.sort(key=lambda g: g.entry_count, reverse=True)

        reused_usernames = sum(
            len(g)
            for g in username_map.values()
            if len(g) >= AuditEngine.REUSED_USERNAME_THRESHOLD
        )

        risk = Counter()
        for finding in report.findings:
            risk[_risk_level(finding)] += 1

        entropy_avg = (
            sum(entropy_values) / len(entropy_values) if entropy_values else 0.0
        )
        entropy_min = min(entropy_values) if entropy_values else 0.0
        entropy_max = max(entropy_values) if entropy_values else 0.0

        access_candidates.sort(key=lambda t: t[0], reverse=True)
        modified_candidates.sort(key=lambda t: t[0], reverse=True)

        score_inputs = ScoreInputs(
            total_entries=len(entries),
            empty_passwords=strength[StrengthBucket.EMPTY.value],
            very_weak=strength[StrengthBucket.VERY_WEAK.value],
            weak=strength[StrengthBucket.WEAK.value],
            fair=strength[StrengthBucket.FAIR.value],
            duplicates=duplicate_total,
            expired=expired_count,
            expiring_7=expiring_7,
            expiring_30=expiring_30,
            expiring_90=expiring_90,
            age_365_plus=age_365_plus,
            empty_usernames=empty_usernames,
            empty_urls=url_empty,
            otp_critical_missing=otp_critical_missing,
            short_passwords=length["under_8"],
            low_entropy=report.low_entropy,
            pwned=report.pwned,
            cert_expired=cert_expired,
            cert_expiring_soon=cert_expiring_soon,
        )
        security_score, label = compute_security_score(score_inputs)

        # Prefer dashboard categories order
        cat_order = [c.value for c in DashboardCategory]
        category_counts = tuple(
            NamedCount(name=name, count=categories[name])
            for name in cat_order
            if categories[name]
        ) + tuple(
            NamedCount(name=name, count=count)
            for name, count in categories.items()
            if name not in cat_order
        )

        top_tags = tuple(
            NamedCount(name=name, count=count)
            for name, count in tags.most_common(12)
        )
        att_type_counts = tuple(
            NamedCount(name=name, count=count)
            for name, count in att_types.most_common()
        )
        att_size_counts = tuple(
            NamedCount(name=label, count=att_sizes[label])
            for label, _, _ in _SIZE_BUCKETS
            if att_sizes[label]
        )
        entropy_buckets = tuple(
            NamedCount(name=label, count=entropy_bucket_counts[label])
            for label, _, _ in _ENTROPY_BUCKETS
        )

        snapshot = DashboardSnapshot(
            audit=report,
            security_score=security_score,
            score_label=label,
            recommendations=(),
            strength_strong=strength[StrengthBucket.STRONG.value],
            strength_good=strength[StrengthBucket.GOOD.value],
            strength_fair=strength[StrengthBucket.FAIR.value],
            strength_weak=strength[StrengthBucket.WEAK.value],
            strength_very_weak=strength[StrengthBucket.VERY_WEAK.value],
            strength_empty=strength[StrengthBucket.EMPTY.value],
            duplicate_password_groups=len(duplicate_groups),
            duplicate_total_reuses=duplicate_total,
            most_reused_password_count=most_reused,
            duplicate_groups=tuple(duplicate_groups[:20]),
            age_0_30=age["0_30"],
            age_30_90=age["30_90"],
            age_90_180=age["90_180"],
            age_180_365=age["180_365"],
            age_365_plus=age["365_plus"],
            age_unknown=age["unknown"],
            expired_count=expired_count,
            expiring_7=expiring_7,
            expiring_30=expiring_30,
            expiring_90=expiring_90,
            entropy_avg=entropy_avg,
            entropy_min=entropy_min,
            entropy_max=entropy_max,
            entropy_buckets=entropy_buckets,
            length_under_8=length["under_8"],
            length_8=length["8"],
            length_12=length["12"],
            length_16=length["16"],
            length_20_plus=length["20_plus"],
            categories=category_counts,
            otp_with=otp_with,
            otp_without=otp_without,
            otp_critical_missing=otp_critical_missing,
            top_tags=top_tags,
            untagged=untagged,
            empty_usernames=empty_usernames,
            reused_usernames=reused_usernames,
            admin_usernames=admin_usernames,
            root_usernames=root_usernames,
            url_empty=url_empty,
            url_https=url_https,
            url_http=url_http,
            url_other=url_other,
            cert_total=cert_total,
            cert_expired=cert_expired,
            cert_expiring_soon=cert_expiring_soon,
            cert_entries=tuple(cert_entries[:20]),
            ssh_rsa=ssh_rsa,
            ssh_ed25519=ssh_ed25519,
            ssh_ecdsa=ssh_ecdsa,
            ssh_other=ssh_other,
            ssh_encrypted=ssh_encrypted,
            ssh_total=ssh_total,
            attachment_types=att_type_counts,
            attachment_size_buckets=att_size_counts,
            attachment_total=attachment_total,
            attachment_total_bytes=attachment_total_bytes,
            favorite_entries=tuple(favorites[:20]),
            recently_accessed=tuple(
                EntryRef(e.uuid, e.title, t.date().isoformat())
                for t, e in access_candidates[:10]
            ),
            recently_modified=tuple(
                EntryRef(e.uuid, e.title, t.date().isoformat())
                for t, e in modified_candidates[:10]
            ),
            total_groups=report.total_groups,
            total_entries=len(entries),
            total_attachments=attachment_total,
            total_otp=otp_with,
            total_certificates=cert_total,
            total_ssh_keys=ssh_total,
            risk_critical=risk["critical"],
            risk_high=risk["high"],
            risk_medium=risk["medium"],
            risk_low=risk["low"],
            findings=report.findings,
        )
        return replace(snapshot, recommendations=build_recommendations(snapshot))
