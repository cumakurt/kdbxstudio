"""Entry and field icon resolution from URL / title / content heuristics."""

from __future__ import annotations

import re
from enum import StrEnum
from urllib.parse import urlparse

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle

from kdbxstudio.core.database import EntryView
from kdbxstudio.ui.icons import standard_icon  # noqa: F401 — re-export convenience


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


_HOST_RULES: tuple[tuple[re.Pattern[str], EntryKind], ...] = (
    (re.compile(r"(gmail|outlook|proton|mail\.|imap|smtp)", re.I), EntryKind.EMAIL),
    (re.compile(r"(github|gitlab|bitbucket|codeberg)", re.I), EntryKind.DEV),
    (re.compile(r"(aws|azure|gcp|cloudflare|digitalocean)", re.I), EntryKind.CLOUD),
    (re.compile(r"(paypal|stripe|visa|mastercard|bank|wise)", re.I), EntryKind.BANK),
    (re.compile(r"(postgres|mysql|mongo|redis|sql)", re.I), EntryKind.DATABASE),
)

_TITLE_RULES: tuple[tuple[re.Pattern[str], EntryKind], ...] = (
    (re.compile(r"\b(ssh|openssh|ed25519|rsa)\b", re.I), EntryKind.SSH),
    (re.compile(r"\b(cert|certificate|x\.?509|pem)\b", re.I), EntryKind.CERTIFICATE),
    (re.compile(r"\b(api|token|bearer|secret key)\b", re.I), EntryKind.API),
    (re.compile(r"\b(wifi|wlan|ssid|router)\b", re.I), EntryKind.WIFI),
    (re.compile(r"\b(card|visa|mastercard|iban|bank)\b", re.I), EntryKind.BANK),
    (re.compile(r"\b(mail|email|inbox)\b", re.I), EntryKind.EMAIL),
    (re.compile(r"\b(note|memo)\b", re.I), EntryKind.NOTE),
    (re.compile(r"\b(db|database|postgres|mysql)\b", re.I), EntryKind.DATABASE),
)

_PEM_SSH = re.compile(r"BEGIN (OPENSSH |RSA |EC |DSA )?PRIVATE KEY", re.I)
_PEM_CERT = re.compile(r"BEGIN CERTIFICATE", re.I)

_KIND_STYLE: dict[EntryKind, QStyle.StandardPixmap] = {
    EntryKind.LOGIN: QStyle.StandardPixmap.SP_ComputerIcon,
    EntryKind.EMAIL: QStyle.StandardPixmap.SP_MessageBoxInformation,
    EntryKind.API: QStyle.StandardPixmap.SP_CommandLink,
    EntryKind.SSH: QStyle.StandardPixmap.SP_ComputerIcon,
    EntryKind.CERTIFICATE: QStyle.StandardPixmap.SP_DialogApplyButton,
    EntryKind.BANK: QStyle.StandardPixmap.SP_DriveHDIcon,
    EntryKind.WIFI: QStyle.StandardPixmap.SP_DriveNetIcon,
    EntryKind.DATABASE: QStyle.StandardPixmap.SP_DirHomeIcon,
    EntryKind.CLOUD: QStyle.StandardPixmap.SP_DriveNetIcon,
    EntryKind.DEV: QStyle.StandardPixmap.SP_FileDialogContentsView,
    EntryKind.NOTE: QStyle.StandardPixmap.SP_FileDialogDetailedView,
    EntryKind.GENERIC: QStyle.StandardPixmap.SP_FileIcon,
}

_FIELD_STYLE: dict[FieldKind, QStyle.StandardPixmap] = {
    FieldKind.TITLE: QStyle.StandardPixmap.SP_FileDialogInfoView,
    FieldKind.USERNAME: QStyle.StandardPixmap.SP_DialogYesButton,
    FieldKind.PASSWORD: QStyle.StandardPixmap.SP_DialogNoButton,
    FieldKind.URL: QStyle.StandardPixmap.SP_DriveNetIcon,
    FieldKind.NOTES: QStyle.StandardPixmap.SP_FileDialogDetailedView,
    FieldKind.CUSTOM: QStyle.StandardPixmap.SP_FileDialogListView,
    FieldKind.OTP: QStyle.StandardPixmap.SP_BrowserReload,
    FieldKind.SHOW: QStyle.StandardPixmap.SP_FileDialogContentsView,
    FieldKind.COPY: QStyle.StandardPixmap.SP_DialogOkButton,
    FieldKind.GENERATE: QStyle.StandardPixmap.SP_BrowserReload,
    FieldKind.SAVE: QStyle.StandardPixmap.SP_DialogSaveButton,
}

# Password-field glyph set varies by detected entry kind.
_PASSWORD_BY_KIND: dict[EntryKind, QStyle.StandardPixmap] = {
    EntryKind.API: QStyle.StandardPixmap.SP_CommandLink,
    EntryKind.SSH: QStyle.StandardPixmap.SP_ComputerIcon,
    EntryKind.CERTIFICATE: QStyle.StandardPixmap.SP_DialogApplyButton,
    EntryKind.BANK: QStyle.StandardPixmap.SP_DriveHDIcon,
    EntryKind.WIFI: QStyle.StandardPixmap.SP_DriveNetIcon,
    EntryKind.DATABASE: QStyle.StandardPixmap.SP_DirHomeIcon,
    EntryKind.EMAIL: QStyle.StandardPixmap.SP_MessageBoxInformation,
    EntryKind.LOGIN: QStyle.StandardPixmap.SP_DialogNoButton,
    EntryKind.DEV: QStyle.StandardPixmap.SP_FileDialogContentsView,
    EntryKind.CLOUD: QStyle.StandardPixmap.SP_DriveNetIcon,
    EntryKind.NOTE: QStyle.StandardPixmap.SP_FileDialogDetailedView,
    EntryKind.GENERIC: QStyle.StandardPixmap.SP_DialogNoButton,
}

_USERNAME_BY_KIND: dict[EntryKind, QStyle.StandardPixmap] = {
    EntryKind.EMAIL: QStyle.StandardPixmap.SP_MessageBoxInformation,
    EntryKind.SSH: QStyle.StandardPixmap.SP_ComputerIcon,
    EntryKind.BANK: QStyle.StandardPixmap.SP_DialogYesButton,
    EntryKind.API: QStyle.StandardPixmap.SP_CommandLink,
}


def _style_icon(pixmap: QStyle.StandardPixmap) -> QIcon:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        style = app.style()
        if style is not None:
            return style.standardIcon(pixmap)
    return QIcon()


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


def entry_kind_icon(kind: EntryKind) -> QIcon:
    return _style_icon(_KIND_STYLE.get(kind, QStyle.StandardPixmap.SP_FileIcon))


def field_icon(field: FieldKind, *, entry_kind: EntryKind | None = None) -> QIcon:
    """Standard icon for a form field; password/username adapt to entry kind."""
    if field is FieldKind.PASSWORD and entry_kind is not None:
        return _style_icon(
            _PASSWORD_BY_KIND.get(entry_kind, QStyle.StandardPixmap.SP_DialogNoButton)
        )
    if field is FieldKind.USERNAME and entry_kind is not None:
        return _style_icon(
            _USERNAME_BY_KIND.get(
                entry_kind, QStyle.StandardPixmap.SP_DialogYesButton
            )
        )
    if field is FieldKind.TITLE and entry_kind is not None:
        return entry_kind_icon(entry_kind)
    return _style_icon(_FIELD_STYLE.get(field, QStyle.StandardPixmap.SP_FileIcon))


def field_icon_name(field: FieldKind) -> str:
    """Stable name for tests / accessibility."""
    return field.value


# Re-export toolbar helpers used alongside field icons
__all__ = [
    "EntryKind",
    "FieldKind",
    "detect_entry_kind",
    "detect_entry_kind_from_view",
    "entry_kind_icon",
    "field_icon",
    "field_icon_name",
    "standard_icon",
]
