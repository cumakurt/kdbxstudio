"""Unit tests for Security Dashboard analyzer and scoring."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.security_dashboard.analyzer import (
    SecurityDashboardAnalyzer,
)
from kdbxstudio.application.security_dashboard.scoring import (
    ScoreInputs,
    compute_security_score,
    score_label,
)
from kdbxstudio.core.password_strength import (
    StrengthBucket,
    estimate_password_strength,
)
from kdbxstudio.core.pem_inspector import inspect_pem_text


def test_score_empty_database() -> None:
    score, label = compute_security_score(ScoreInputs(total_entries=0))
    assert score == 100
    assert label == "Excellent"


def test_score_penalties_and_labels() -> None:
    score, label = compute_security_score(
        ScoreInputs(
            total_entries=10,
            empty_passwords=2,
            weak=2,
            duplicates=4,
            expired=1,
        )
    )
    assert 0 <= score < 100
    assert label == score_label(score)


def test_password_strength_buckets() -> None:
    assert estimate_password_strength("")[1] is StrengthBucket.EMPTY
    assert estimate_password_strength("abc")[1] in {
        StrengthBucket.VERY_WEAK,
        StrengthBucket.WEAK,
    }
    strong = estimate_password_strength("Tr0ub4dor&3-Extra-Long!!")
    assert strong[0] >= 60


def test_openssh_ed25519_detection() -> None:
    # Minimal openssh-key-v1 header with cipher none + one ed25519 pubkey blob
    import base64
    import struct

    def ssh_str(data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + data

    pubkey = ssh_str(b"ssh-ed25519") + ssh_str(b"\x00" * 32)
    payload = (
        b"openssh-key-v1\0"
        + ssh_str(b"none")
        + ssh_str(b"none")
        + ssh_str(b"")
        + struct.pack(">I", 1)
        + ssh_str(pubkey)
        + ssh_str(b"")
    )
    body = base64.b64encode(payload).decode("ascii")
    pem = (
        "-----BEGIN OPENSSH PRIVATE KEY-----\n"
        + "\n".join(body[i : i + 64] for i in range(0, len(body), 64))
        + "\n-----END OPENSSH PRIVATE KEY-----\n"
    )
    blocks = inspect_pem_text(pem)
    assert len(blocks) == 1
    assert blocks[0].kind == "private_key"
    assert blocks[0].algorithm == "ed25519"
    assert blocks[0].encrypted is False


def test_certificate_not_after_heuristic() -> None:
    # Synthetic DER-like blob embedding GeneralizedTime
    import base64

    der = b"\x30\x82" + b"\x00" * 20 + b"20200101000000Z" + b"20301231235959Z"
    body = base64.b64encode(der).decode("ascii")
    pem = "-----BEGIN CERTIFICATE-----\n" + body + "\n-----END CERTIFICATE-----\n"
    blocks = inspect_pem_text(pem)
    assert blocks[0].kind == "certificate"
    assert "2030" in blocks[0].not_after or blocks[0].not_after == ""


def test_analyzer_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "dash.kdbx"
    dbm = DatabaseManager()
    dbm.create(db_path, "secret")
    root = dbm.root_group_uuid()
    assert root is not None
    weak = dbm.add_entry(root, title="Weak", username="admin", password="abc")
    strong = dbm.add_entry(
        root,
        title="Strong",
        username="user",
        password="Correct-Horse-Battery-Staple-99!",
        url="https://example.com",
        tags=["favorite"],
    )
    dbm.update_entry(
        strong.uuid,
        otp="otpauth://totp/Example:user?secret=JBSWY3DPEHPK3PXP&issuer=Example",
    )
    dbm.add_entry(
        root,
        title="Dup1",
        username="a",
        password="same-password-value",
        url="http://insecure.example",
    )
    dbm.add_entry(
        root,
        title="Dup2",
        username="b",
        password="same-password-value",
    )
    soon = datetime.now(UTC) + timedelta(days=5)
    dbm.update_entry(weak.uuid, expires=True, expiry_time=soon)

    analyzer = SecurityDashboardAnalyzer(dbm)
    snap = analyzer.run()
    assert snap.total_entries >= 4
    assert 0 <= snap.security_score <= 100
    assert snap.score_label
    assert snap.duplicate_password_groups >= 1
    assert snap.strength_empty == 0
    assert snap.otp_with >= 1
    assert snap.url_https >= 1
    assert snap.url_http >= 1
    assert snap.admin_usernames >= 1
    assert snap.favorite_entries
    assert snap.recommendations
    entries = dbm.all_entries()
    assert any(e.modified for e in entries)
