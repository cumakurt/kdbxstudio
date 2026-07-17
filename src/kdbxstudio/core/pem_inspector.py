"""PEM / SSH / certificate field inspection (stdlib only)."""

from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass

_PEM_BLOCK = re.compile(
    r"-----BEGIN ([A-Z0-9 ]+)-----\r?\n(.+?)\r?\n-----END \1-----",
    re.DOTALL,
)


@dataclass(frozen=True)
class PemBlockInfo:
    label: str
    kind: str
    sha256: str
    size_bytes: int
    line_count: int


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


def inspect_pem_text(text: str) -> list[PemBlockInfo]:
    """Extract PEM blocks and compute content fingerprints."""
    results: list[PemBlockInfo] = []
    for match in _PEM_BLOCK.finditer(text or ""):
        label = match.group(1).strip()
        body = match.group(2)
        # Strip whitespace from base64 body for hashing
        b64 = re.sub(r"\s+", "", body)
        try:
            raw = base64.b64decode(b64, validate=False)
        except Exception:
            raw = b64.encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        results.append(
            PemBlockInfo(
                label=label,
                kind=classify_pem_kind(label),
                sha256=digest,
                size_bytes=len(raw),
                line_count=body.count("\n") + 1,
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
                "",
            ]
        )
    return "\n".join(lines).rstrip()
