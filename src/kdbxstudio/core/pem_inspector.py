"""PEM / SSH / certificate field inspection (stdlib only)."""

from __future__ import annotations

import base64
import hashlib
import re
import struct
from dataclasses import dataclass
from datetime import UTC, datetime

_PEM_BLOCK = re.compile(
    r"-----BEGIN ([A-Z0-9 ]+)-----\r?\n(.+?)\r?\n-----END \1-----",
    re.DOTALL,
)

# ASN.1 UTCTime YYMMDDHHMMSSZ / GeneralizedTime YYYYMMDDHHMMSSZ
_ASN1_TIME = re.compile(
    rb"(?:(?P<utc>\d{12}Z)|(?P<gen>\d{14}Z))"
)


@dataclass(frozen=True)
class PemBlockInfo:
    label: str
    kind: str
    sha256: str
    size_bytes: int
    line_count: int
    algorithm: str = ""
    encrypted: bool = False
    not_before: str = ""
    not_after: str = ""


def classify_pem_kind(label: str) -> str:
    upper = label.upper()
    if "CERTIFICATE" in upper and "REQUEST" not in upper:
        return "certificate"
    if "PRIVATE KEY" in upper or "OPENSSH PRIVATE KEY" in upper:
        return "private_key"
    if "PUBLIC KEY" in upper:
        return "public_key"
    if "CERTIFICATE REQUEST" in upper or "CSR" in upper:
        return "csr"
    return "pem"


def _decode_pem_body(body: str) -> bytes:
    b64 = re.sub(r"\s+", "", body)
    try:
        return base64.b64decode(b64, validate=False)
    except Exception:
        return b64.encode("utf-8")


def _parse_asn1_time(raw: bytes) -> str:
    """Parse ASN.1 UTCTime/GeneralizedTime bytes to ISO-8601 UTC string."""
    text = raw.decode("ascii", errors="ignore")
    try:
        if len(text) == 13 and text.endswith("Z"):  # UTCTime YYMMDDHHMMSSZ
            yy = int(text[0:2])
            year = 2000 + yy if yy < 50 else 1900 + yy
            dt = datetime(
                year,
                int(text[2:4]),
                int(text[4:6]),
                int(text[6:8]),
                int(text[8:10]),
                int(text[10:12]),
                tzinfo=UTC,
            )
            return dt.isoformat()
        if len(text) == 15 and text.endswith("Z"):  # GeneralizedTime
            dt = datetime(
                int(text[0:4]),
                int(text[4:6]),
                int(text[6:8]),
                int(text[8:10]),
                int(text[10:12]),
                int(text[12:14]),
                tzinfo=UTC,
            )
            return dt.isoformat()
    except (ValueError, OverflowError):
        return ""
    return ""


def _extract_cert_validity(der: bytes) -> tuple[str, str]:
    """Best-effort NotBefore/NotAfter from DER certificate bytes."""
    times: list[str] = []
    for match in _ASN1_TIME.finditer(der):
        blob = match.group("utc") or match.group("gen")
        if blob is None:
            continue
        parsed = _parse_asn1_time(blob)
        if parsed:
            times.append(parsed)
        if len(times) >= 2:
            break
    if len(times) >= 2:
        return times[0], times[1]
    if len(times) == 1:
        return "", times[0]
    return "", ""


def _read_openssh_string(data: bytes, offset: int) -> tuple[bytes, int]:
    if offset + 4 > len(data):
        return b"", offset
    (length,) = struct.unpack(">I", data[offset : offset + 4])
    offset += 4
    end = offset + length
    if end > len(data) or length > len(data):
        return b"", offset
    return data[offset:end], end


def _inspect_openssh_private_key(raw: bytes) -> tuple[str, bool]:
    """Return (algorithm, encrypted) for OpenSSH private key payload."""
    magic = b"openssh-key-v1\0"
    if not raw.startswith(magic):
        return "unknown", False
    offset = len(magic)
    ciphername, offset = _read_openssh_string(raw, offset)
    _kdfname, offset = _read_openssh_string(raw, offset)
    _kdf, offset = _read_openssh_string(raw, offset)
    encrypted = ciphername not in (b"", b"none")
    if offset + 4 > len(raw):
        return "unknown", encrypted
    (nkeys,) = struct.unpack(">I", raw[offset : offset + 4])
    offset += 4
    if nkeys < 1:
        return "unknown", encrypted
    pubkey, _ = _read_openssh_string(raw, offset)
    algo_bytes, _ = _read_openssh_string(pubkey, 0)
    algo = algo_bytes.decode("ascii", errors="ignore").lower()
    if "ed25519" in algo:
        return "ed25519", encrypted
    if "ecdsa" in algo:
        return "ecdsa", encrypted
    if "rsa" in algo:
        return "rsa", encrypted
    if "dss" in algo or "dsa" in algo:
        return "dsa", encrypted
    return algo or "unknown", encrypted


def _inspect_traditional_key(label: str, pem_text: str, raw: bytes) -> tuple[str, bool]:
    upper = label.upper()
    encrypted = bool(
        re.search(r"Proc-Type:\s*4,\s*ENCRYPTED", pem_text, re.I)
        or re.search(r"ENCRYPTED", upper)
    )
    if "RSA" in upper:
        return "rsa", encrypted
    if "EC" in upper or "ECDSA" in upper:
        return "ecdsa", encrypted
    if "DSA" in upper:
        return "dsa", encrypted
    # PKCS#8: peek at algorithm OID bytes (best-effort)
    if b"\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01" in raw:  # rsaEncryption
        return "rsa", encrypted
    if b"ed25519" in raw.lower() or b"\x2b\x65\x70" in raw:
        return "ed25519", encrypted
    if b"\x2a\x86\x48\xce\x3d\x02\x01" in raw:  # ecPublicKey
        return "ecdsa", encrypted
    return "unknown", encrypted


def inspect_pem_text(text: str) -> list[PemBlockInfo]:
    """Extract PEM blocks and compute content fingerprints / key metadata."""
    results: list[PemBlockInfo] = []
    for match in _PEM_BLOCK.finditer(text or ""):
        label = match.group(1).strip()
        body = match.group(2)
        full = match.group(0)
        raw = _decode_pem_body(body)
        digest = hashlib.sha256(raw).hexdigest()
        kind = classify_pem_kind(label)
        algorithm = ""
        encrypted = False
        not_before = ""
        not_after = ""
        if kind == "private_key":
            if "OPENSSH" in label.upper():
                algorithm, encrypted = _inspect_openssh_private_key(raw)
            else:
                algorithm, encrypted = _inspect_traditional_key(label, full, raw)
        elif kind == "certificate":
            not_before, not_after = _extract_cert_validity(raw)
        results.append(
            PemBlockInfo(
                label=label,
                kind=kind,
                sha256=digest,
                size_bytes=len(raw),
                line_count=body.count("\n") + 1,
                algorithm=algorithm,
                encrypted=encrypted,
                not_before=not_before,
                not_after=not_after,
            )
        )
    return results


def format_pem_report(blocks: list[PemBlockInfo]) -> str:
    if not blocks:
        return "No PEM blocks detected."
    lines: list[str] = []
    for index, block in enumerate(blocks, start=1):
        lines.extend(
            [
                f"Block {index}: {block.label}",
                f"  Kind: {block.kind}",
                f"  Size: {block.size_bytes} bytes",
                f"  Lines: {block.line_count}",
                f"  SHA-256: {block.sha256}",
            ]
        )
        if block.algorithm:
            lines.append(f"  Algorithm: {block.algorithm}")
        if block.kind == "private_key":
            lines.append(f"  Encrypted: {'yes' if block.encrypted else 'no'}")
        if block.not_before:
            lines.append(f"  Not before: {block.not_before}")
        if block.not_after:
            lines.append(f"  Not after: {block.not_after}")
        lines.append("")
    return "\n".join(lines).rstrip()
