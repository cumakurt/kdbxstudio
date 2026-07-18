"""Entry and field icon resolution from URL / title / content heuristics."""

from __future__ import annotations

import re
from enum import StrEnum
from urllib.parse import urlparse

from PySide6.QtGui import QIcon

from kdbxstudio.core.database import EntryView
from kdbxstudio.ui.icons import icon, standard_icon

__all__ = [
    "EntryKind",
    "FieldKind",
    "detect_entry_kind",
    "detect_entry_kind_from_view",
    "entry_kind_icon",
    "field_icon",
    "field_icon_name",
    "category_icon_name",
    "standard_icon",
]


class EntryKind(StrEnum):
    LOGIN = "login"
    EMAIL = "email"
    API = "api"
    SSH = "ssh"
    CERTIFICATE = "certificate"
    BANK = "bank"
    WIFI = "wifi"
    DATABASE = "database"
    CLOUD = "cloud"
    DEV = "dev"
    NOTE = "note"
    SERVER = "server"
    VPN = "vpn"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    LINUX = "linux"
    WINDOWS = "windows"
    IDENTITY = "identity"
    CRYPTO = "crypto"
    LICENSE = "license"
    GENERIC = "generic"


class FieldKind(StrEnum):
    TITLE = "title"
    USERNAME = "username"
    PASSWORD = "password"
    URL = "url"
    NOTES = "notes"
    CUSTOM = "custom"
    OTP = "otp"
    SHOW = "show"
    COPY = "copy"
    GENERATE = "generate"
    SAVE = "save"
    ATTACHMENT = "attachment"


_HOST_RULES: tuple[tuple[re.Pattern[str], EntryKind], ...] = (
    (re.compile(r"(gmail|outlook|proton|mail\.|imap|smtp)", re.I), EntryKind.EMAIL),
    (re.compile(r"(github|gitlab|bitbucket|codeberg)", re.I), EntryKind.DEV),
    (re.compile(r"(aws|azure|gcp|cloudflare|digitalocean)", re.I), EntryKind.CLOUD),
    (re.compile(r"(paypal|stripe|visa|mastercard|bank|wise)", re.I), EntryKind.BANK),
    (re.compile(r"(postgres|mysql|mongo|redis|sql)", re.I), EntryKind.DATABASE),
    (re.compile(r"(docker|hub\.docker)", re.I), EntryKind.DOCKER),
    (re.compile(r"(k8s|kubernetes)", re.I), EntryKind.KUBERNETES),
)

_TITLE_RULES: tuple[tuple[re.Pattern[str], EntryKind], ...] = (
    (re.compile(r"\b(ssh|openssh|ed25519|rsa)\b", re.I), EntryKind.SSH),
    (re.compile(r"\b(cert|certificate|x\.?509|pem)\b", re.I), EntryKind.CERTIFICATE),
    (re.compile(r"\b(api|token|bearer|secret key)\b", re.I), EntryKind.API),
    (re.compile(r"\b(wifi|wlan|ssid|router)\b", re.I), EntryKind.WIFI),
    (re.compile(r"\b(vpn|wireguard|openvpn)\b", re.I), EntryKind.VPN),
    (re.compile(r"\b(docker)\b", re.I), EntryKind.DOCKER),
    (re.compile(r"\b(kubernetes|k8s)\b", re.I), EntryKind.KUBERNETES),
    (re.compile(r"\b(linux|ubuntu|debian|fedora)\b", re.I), EntryKind.LINUX),
    (re.compile(r"\b(windows|win\.?server)\b", re.I), EntryKind.WINDOWS),
    (re.compile(r"\b(server|vps|host)\b", re.I), EntryKind.SERVER),
    (re.compile(r"\b(identity|sso|oauth|saml)\b", re.I), EntryKind.IDENTITY),
    (re.compile(r"\b(crypto|wallet|bitcoin|ethereum)\b", re.I), EntryKind.CRYPTO),
    (re.compile(r"\b(license|licence|serial)\b", re.I), EntryKind.LICENSE),
    (re.compile(r"\b(card|visa|mastercard|iban|bank)\b", re.I), EntryKind.BANK),
    (re.compile(r"\b(mail|email|inbox)\b", re.I), EntryKind.EMAIL),
    (re.compile(r"\b(note|memo)\b", re.I), EntryKind.NOTE),
    (re.compile(r"\b(db|database|postgres|mysql)\b", re.I), EntryKind.DATABASE),
)

_PEM_SSH = re.compile(r"BEGIN (OPENSSH |RSA |EC |DSA )?PRIVATE KEY", re.I)
_PEM_CERT = re.compile(r"BEGIN CERTIFICATE", re.I)

_KIND_ICON: dict[EntryKind, str] = {
    EntryKind.LOGIN: "language",
    EntryKind.EMAIL: "mail",
    EntryKind.API: "api",
    EntryKind.SSH: "terminal",
    EntryKind.CERTIFICATE: "verified_user",
    EntryKind.BANK: "account_balance",
    EntryKind.WIFI: "wifi",
    EntryKind.DATABASE: "database",
    EntryKind.CLOUD: "cloud",
    EntryKind.DEV: "code",
    EntryKind.NOTE: "sticky_note",
    EntryKind.SERVER: "dns",
    EntryKind.VPN: "vpn_lock",
    EntryKind.DOCKER: "deployed_code",
    EntryKind.KUBERNETES: "hub",
    EntryKind.LINUX: "computer",
    EntryKind.WINDOWS: "window",
    EntryKind.IDENTITY: "badge",
    EntryKind.CRYPTO: "currency_bitcoin",
    EntryKind.LICENSE: "license",
    EntryKind.GENERIC: "password",
}

_FIELD_ICON: dict[FieldKind, str] = {
    FieldKind.TITLE: "article",
    FieldKind.USERNAME: "person",
    FieldKind.PASSWORD: "password",
    FieldKind.URL: "link",
    FieldKind.NOTES: "sticky_note",
    FieldKind.CUSTOM: "edit",
    FieldKind.OTP: "pin",
    FieldKind.SHOW: "visibility",
    FieldKind.COPY: "content_copy",
    FieldKind.GENERATE: "refresh",
    FieldKind.SAVE: "save",
    FieldKind.ATTACHMENT: "attach_file",
}

_PASSWORD_BY_KIND: dict[EntryKind, str] = {
    EntryKind.API: "api",
    EntryKind.SSH: "terminal",
    EntryKind.CERTIFICATE: "verified_user",
    EntryKind.BANK: "account_balance",
    EntryKind.WIFI: "wifi",
    EntryKind.DATABASE: "database",
    EntryKind.EMAIL: "mail",
    EntryKind.LOGIN: "password",
    EntryKind.DEV: "code",
    EntryKind.CLOUD: "cloud",
    EntryKind.NOTE: "sticky_note",
    EntryKind.VPN: "vpn_lock",
    EntryKind.CRYPTO: "key",
    EntryKind.GENERIC: "password",
}

_USERNAME_BY_KIND: dict[EntryKind, str] = {
    EntryKind.EMAIL: "mail",
    EntryKind.SSH: "terminal",
    EntryKind.BANK: "person",
    EntryKind.API: "api",
    EntryKind.IDENTITY: "badge",
}


def detect_entry_kind(
    *,
    title: str = "",
    url: str = "",
    username: str = "",
    notes: str = "",
    custom_properties: dict[str, str] | None = None,
) -> EntryKind:
    """Infer entry category from fields (custom Type, PEM, URL host, title)."""
    props = custom_properties or {}
    type_hint = (props.get("Type") or props.get("type") or "").strip().lower()
    type_map = {
        "api key": EntryKind.API,
        "api": EntryKind.API,
        "ssh key": EntryKind.SSH,
        "ssh": EntryKind.SSH,
        "certificate": EntryKind.CERTIFICATE,
        "bank card": EntryKind.BANK,
        "secure note": EntryKind.NOTE,
        "note": EntryKind.NOTE,
        "login": EntryKind.LOGIN,
        "vpn": EntryKind.VPN,
        "docker": EntryKind.DOCKER,
        "server": EntryKind.SERVER,
        "license": EntryKind.LICENSE,
    }
    if type_hint in type_map:
        return type_map[type_hint]

    blob = f"{notes}\n{props.get('private_key', '')}\n{props.get('Private Key', '')}"
    if _PEM_SSH.search(blob):
        return EntryKind.SSH
    if _PEM_CERT.search(blob):
        return EntryKind.CERTIFICATE

    host = ""
    if url.strip():
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = (parsed.hostname or "").lower()
    hay = f"{title} {username} {host} {url}"
    for pattern, kind in _HOST_RULES:
        if host and pattern.search(host):
            return kind
        if pattern.search(hay):
            return kind
    for pattern, kind in _TITLE_RULES:
        if pattern.search(hay):
            return kind

    if url.strip() or username.strip():
        return EntryKind.LOGIN
    if notes.strip() and not url.strip():
        return EntryKind.NOTE
    return EntryKind.GENERIC


def detect_entry_kind_from_view(entry: EntryView) -> EntryKind:
    return detect_entry_kind(
        title=entry.title,
        url=entry.url,
        username=entry.username,
        notes=entry.notes,
        custom_properties=entry.custom_properties,
    )


def category_icon_name(kind: EntryKind) -> str:
    return _KIND_ICON.get(kind, "password")


def entry_kind_icon(kind: EntryKind, *, size: int = 18) -> QIcon:
    return icon(category_icon_name(kind), size=size)


def field_icon(
    field: FieldKind,
    *,
    entry_kind: EntryKind | None = None,
    size: int = 18,
) -> QIcon:
    """Outlined icon for a form field; password/username adapt to entry kind."""
    if field is FieldKind.PASSWORD and entry_kind is not None:
        return icon(_PASSWORD_BY_KIND.get(entry_kind, "password"), size=size)
    if field is FieldKind.USERNAME and entry_kind is not None:
        return icon(_USERNAME_BY_KIND.get(entry_kind, "person"), size=size)
    if field is FieldKind.TITLE and entry_kind is not None:
        return entry_kind_icon(entry_kind, size=size)
    return icon(_FIELD_ICON.get(field, "edit"), size=size)


def field_icon_name(field: FieldKind) -> str:
    """Stable name for tests / accessibility."""
    return field.value
