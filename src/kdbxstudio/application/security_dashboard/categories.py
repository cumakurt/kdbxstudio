"""Dashboard category detection from entry fields (UI-independent)."""

from __future__ import annotations

import re
from enum import StrEnum
from urllib.parse import urlparse

from kdbxstudio.core.database import EntryView

_PEM_SSH = re.compile(r"BEGIN (OPENSSH |RSA |EC |DSA )?PRIVATE KEY", re.I)
_PEM_CERT = re.compile(r"BEGIN CERTIFICATE", re.I)


class DashboardCategory(StrEnum):
    SERVER = "server"
    SSH = "ssh"
    VPN = "vpn"
    API = "api"
    WEBSITE = "website"
    CLOUD = "cloud"
    DATABASE = "database"
    WIFI = "wifi"
    CERTIFICATE = "certificate"
    LICENSE = "license"
    OTHER = "other"


_HOST_RULES: tuple[tuple[re.Pattern[str], DashboardCategory], ...] = (
    (
        re.compile(r"(aws|azure|gcp|cloudflare|digitalocean)", re.I),
        DashboardCategory.CLOUD,
    ),
    (
        re.compile(r"(postgres|mysql|mongo|redis|sql)", re.I),
        DashboardCategory.DATABASE,
    ),
)

_TITLE_RULES: tuple[tuple[re.Pattern[str], DashboardCategory], ...] = (
    (re.compile(r"\b(ssh|openssh|ed25519)\b", re.I), DashboardCategory.SSH),
    (
        re.compile(r"\b(cert|certificate|x\.?509|pem)\b", re.I),
        DashboardCategory.CERTIFICATE,
    ),
    (re.compile(r"\b(api|token|bearer|secret key)\b", re.I), DashboardCategory.API),
    (
        re.compile(r"\b(vpn|openvpn|wireguard|tailscale)\b", re.I),
        DashboardCategory.VPN,
    ),
    (re.compile(r"\b(wifi|wlan|ssid|router)\b", re.I), DashboardCategory.WIFI),
    (
        re.compile(r"\b(server|vps|host|bare.?metal)\b", re.I),
        DashboardCategory.SERVER,
    ),
    (
        re.compile(r"\b(license|licence|serial|activation)\b", re.I),
        DashboardCategory.LICENSE,
    ),
    (
        re.compile(r"\b(db|database|postgres|mysql)\b", re.I),
        DashboardCategory.DATABASE,
    ),
    (re.compile(r"\b(cloud|s3|blob)\b", re.I), DashboardCategory.CLOUD),
)

_CRITICAL_FOR_OTP = frozenset(
    {
        DashboardCategory.WEBSITE,
        DashboardCategory.API,
        DashboardCategory.CLOUD,
        DashboardCategory.SERVER,
        DashboardCategory.VPN,
    }
)


def detect_dashboard_category(
    *,
    title: str = "",
    url: str = "",
    username: str = "",
    notes: str = "",
    custom_properties: dict[str, str] | None = None,
) -> DashboardCategory:
    props = custom_properties or {}
    type_hint = (props.get("Type") or props.get("type") or "").strip().lower()
    type_map = {
        "api key": DashboardCategory.API,
        "api": DashboardCategory.API,
        "ssh key": DashboardCategory.SSH,
        "ssh": DashboardCategory.SSH,
        "certificate": DashboardCategory.CERTIFICATE,
        "license": DashboardCategory.LICENSE,
        "vpn": DashboardCategory.VPN,
        "wifi": DashboardCategory.WIFI,
        "server": DashboardCategory.SERVER,
        "cloud": DashboardCategory.CLOUD,
        "database": DashboardCategory.DATABASE,
        "login": DashboardCategory.WEBSITE,
    }
    if type_hint in type_map:
        return type_map[type_hint]

    blob = f"{notes}\n{props.get('private_key', '')}\n{props.get('Private Key', '')}"
    if _PEM_SSH.search(blob):
        return DashboardCategory.SSH
    if _PEM_CERT.search(blob):
        return DashboardCategory.CERTIFICATE

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
    if url.strip():
        return DashboardCategory.WEBSITE
    return DashboardCategory.OTHER


def detect_category_from_view(entry: EntryView) -> DashboardCategory:
    return detect_dashboard_category(
        title=entry.title,
        url=entry.url,
        username=entry.username,
        notes=entry.notes,
        custom_properties=entry.custom_properties,
    )


def is_critical_for_otp(category: DashboardCategory) -> bool:
    return category in _CRITICAL_FOR_OTP
