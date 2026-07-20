"""Tests for PEM inspector and secret templates."""

from kdbxstudio.application.templates import get_template, list_templates
from kdbxstudio.core.pem_inspector import inspect_pem_text


def test_list_templates() -> None:
    templates = list_templates()
    assert len(templates) >= 4
    assert get_template("ssh_key") is not None
    assert get_template("missing") is None


def test_inspect_pem_certificate() -> None:
    # Minimal fake PEM (not a real cert) — base64 of "hello"
    pem = "-----BEGIN CERTIFICATE-----\naGVsbG8=\n-----END CERTIFICATE-----\n"
    blocks = inspect_pem_text(pem)
    assert len(blocks) == 1
    assert blocks[0].kind == "certificate"
    assert len(blocks[0].sha256) == 64


def test_inspect_openssh_key() -> None:
    pem = (
        "-----BEGIN OPENSSH PRIVATE KEY-----\n"
        "cHJpdmF0ZQ==\n"
        "-----END OPENSSH PRIVATE KEY-----\n"
    )
    blocks = inspect_pem_text(pem)
    assert blocks[0].kind == "private_key"
