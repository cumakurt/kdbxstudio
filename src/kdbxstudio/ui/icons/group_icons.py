"""Colorful category icons for Groups tree — auto-assigned from group names."""

from __future__ import annotations

import re
from collections.abc import Callable
from enum import StrEnum
from functools import lru_cache

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


class GroupKind(StrEnum):
    HOME = "home"
    FOLDER = "folder"
    INTERNET = "internet"
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    SERVER = "server"
    CLOUD = "cloud"
    VPN = "vpn"
    SSH = "ssh"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    DATABASE = "database"
    EMAIL = "email"
    BANK = "bank"
    WIFI = "wifi"
    CRYPTO = "crypto"
    IDENTITY = "identity"
    API = "api"
    CERTIFICATE = "certificate"
    DEV = "dev"
    NOTE = "note"
    LICENSE = "license"
    RECYCLE = "recycle"


# Soft brand colors for category badges (dark-mode friendly).
_KIND_COLORS: dict[GroupKind, str] = {
    GroupKind.HOME: "#3D9A9C",
    GroupKind.FOLDER: "#64748B",
    GroupKind.INTERNET: "#3B82F6",
    GroupKind.WINDOWS: "#0078D4",
    GroupKind.LINUX: "#E95420",
    GroupKind.MACOS: "#94A3B8",
    GroupKind.SERVER: "#6366F1",
    GroupKind.CLOUD: "#06B6D4",
    GroupKind.VPN: "#8B5CF6",
    GroupKind.SSH: "#10B981",
    GroupKind.DOCKER: "#2496ED",
    GroupKind.KUBERNETES: "#326CE5",
    GroupKind.DATABASE: "#F59E0B",
    GroupKind.EMAIL: "#EC4899",
    GroupKind.BANK: "#059669",
    GroupKind.WIFI: "#14B8A6",
    GroupKind.CRYPTO: "#F97316",
    GroupKind.IDENTITY: "#78716C",
    GroupKind.API: "#0EA5E9",
    GroupKind.CERTIFICATE: "#84CC16",
    GroupKind.DEV: "#A855F7",
    GroupKind.NOTE: "#FBBF24",
    GroupKind.LICENSE: "#22C55E",
    GroupKind.RECYCLE: "#EF4444",
}

# (pattern, kind) — first match wins; names matched case-insensitively.
_NAME_RULES: tuple[tuple[re.Pattern[str], GroupKind], ...] = (
    (re.compile(r"(recycle|trash|bin|çöp|geri\s*dönüşüm)", re.I), GroupKind.RECYCLE),
    (
        re.compile(
            r"(internet|web|www|website|browser|http|site|online)",
            re.I,
        ),
        GroupKind.INTERNET,
    ),
    (
        re.compile(r"(windows|win\b|microsoft|pc\b|win11|win10)", re.I),
        GroupKind.WINDOWS,
    ),
    (
        re.compile(
            r"(linux|ubuntu|debian|fedora|arch|centos|rhel|unix|gnu)",
            re.I,
        ),
        GroupKind.LINUX,
    ),
    (re.compile(r"(mac\b|macos|osx|apple|iphone|ipad)", re.I), GroupKind.MACOS),
    (
        re.compile(r"(server|vps|hosting|datacenter|bare[\s-]?metal)", re.I),
        GroupKind.SERVER,
    ),
    (
        re.compile(
            r"(cloud|aws|azure|gcp|digitalocean|cloudflare|s3\b)",
            re.I,
        ),
        GroupKind.CLOUD,
    ),
    (
        re.compile(r"(vpn|wireguard|openvpn|tailscale|zerotier)", re.I),
        GroupKind.VPN,
    ),
    (re.compile(r"(ssh|shell|terminal|console|putty)", re.I), GroupKind.SSH),
    (re.compile(r"(docker|container|compose)", re.I), GroupKind.DOCKER),
    (re.compile(r"(kubernetes|k8s|helm|kubect)", re.I), GroupKind.KUBERNETES),
    (
        re.compile(
            r"(database|db\b|sql|postgres|mysql|mongo|redis|mariadb|oracle)",
            re.I,
        ),
        GroupKind.DATABASE,
    ),
    (
        re.compile(r"(mail|email|e-mail|inbox|smtp|imap|outlook|gmail)", re.I),
        GroupKind.EMAIL,
    ),
    (
        re.compile(
            r"(crypto|bitcoin|ethereum|btc\b|eth\b|blockchain|wallet)",
            re.I,
        ),
        GroupKind.CRYPTO,
    ),
    (
        re.compile(
            r"(bank|finance|card|iban|paypal|stripe|ödeme|finans)",
            re.I,
        ),
        GroupKind.BANK,
    ),
    (re.compile(r"(wifi|wi-fi|wlan|network|lan\b|router|ssid)", re.I), GroupKind.WIFI),
    (
        re.compile(r"(identity|sso|oauth|saml|ldap|active\s*directory|ad\b)", re.I),
        GroupKind.IDENTITY,
    ),
    (re.compile(r"(api|token|bearer|webhook|graphql|rest)", re.I), GroupKind.API),
    (
        re.compile(r"(cert|certificate|ssl|tls|x\.?509|pem|ca\b)", re.I),
        GroupKind.CERTIFICATE,
    ),
    (
        re.compile(r"(dev|develop|code|git|github|gitlab|programming)", re.I),
        GroupKind.DEV,
    ),
    (re.compile(r"(note|notes|memo|journal|notlar)", re.I), GroupKind.NOTE),
    (re.compile(r"(license|licence|serial|lisans)", re.I), GroupKind.LICENSE),
    (re.compile(r"(home|general|root|kişisel|personal|genel)", re.I), GroupKind.HOME),
)


def detect_group_kind(name: str, *, is_recycle_bin: bool = False) -> GroupKind:
    """Infer a category icon from the group display name."""
    if is_recycle_bin:
        return GroupKind.RECYCLE
    text = (name or "").strip()
    if not text:
        return GroupKind.FOLDER
    for pattern, kind in _NAME_RULES:
        if pattern.search(text):
            return kind
    return GroupKind.FOLDER


def group_kind_color(kind: GroupKind) -> str:
    return _KIND_COLORS.get(kind, _KIND_COLORS[GroupKind.FOLDER])


def _pen(color: QColor, width: float = 1.6) -> QPen:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _badge(p: QPainter, color: QColor) -> None:
    """Rounded square badge background."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawRoundedRect(QRectF(1.5, 1.5, 21, 21), 5, 5)


def _fg() -> QColor:
    return QColor("#FFFFFF")


def _paint_home(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(12, 6)
    path.lineTo(19, 12)
    path.lineTo(17, 12)
    path.lineTo(17, 18)
    path.lineTo(7, 18)
    path.lineTo(7, 12)
    path.lineTo(5, 12)
    path.closeSubpath()
    p.drawPath(path)


def _paint_folder(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(5, 10)
    path.lineTo(5, 8.5)
    path.lineTo(9, 8.5)
    path.lineTo(10.5, 7)
    path.lineTo(18, 7)
    path.lineTo(18, 17)
    path.lineTo(5, 17)
    path.closeSubpath()
    p.drawPath(path)


def _paint_internet(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(12, 12), 6.5, 6.5)
    p.drawLine(QPointF(5.5, 12), QPointF(18.5, 12))
    path = QPainterPath()
    path.moveTo(12, 5.5)
    path.cubicTo(15, 8.5, 15, 15.5, 12, 18.5)
    path.moveTo(12, 5.5)
    path.cubicTo(9, 8.5, 9, 15.5, 12, 18.5)
    p.drawPath(path)


def _paint_windows(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_fg())
    gap = 1.2
    s = 5.2
    p.drawRoundedRect(QRectF(6, 6, s, s), 0.8, 0.8)
    p.drawRoundedRect(QRectF(6 + s + gap, 6, s, s), 0.8, 0.8)
    p.drawRoundedRect(QRectF(6, 6 + s + gap, s, s), 0.8, 0.8)
    p.drawRoundedRect(QRectF(6 + s + gap, 6 + s + gap, s, s), 0.8, 0.8)


def _paint_linux(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Simplified Tux-like oval head + body
    p.drawEllipse(QPointF(12, 9), 4, 3.5)
    path = QPainterPath()
    path.moveTo(8, 12)
    path.cubicTo(7, 18, 17, 18, 16, 12)
    p.drawPath(path)
    p.setBrush(_fg())
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(10.5, 9), 0.8, 0.8)
    p.drawEllipse(QPointF(13.5, 9), 0.8, 0.8)


def _paint_macos(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Apple-ish silhouette (simplified oval + bite)
    path = QPainterPath()
    path.addEllipse(QPointF(12, 13), 5.5, 6)
    p.drawPath(path)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(c)  # bite using badge color
    p.drawEllipse(QPointF(16.5, 10), 2.2, 2.2)
    p.setPen(_pen(_fg(), 1.4))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(12, 5.5), QPointF(13.5, 8))


def _paint_server(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.4))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(5, 6, 14, 5), 1.2, 1.2)
    p.drawRoundedRect(QRectF(5, 13, 14, 5), 1.2, 1.2)
    p.setBrush(_fg())
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(8, 8.5), 0.9, 0.9)
    p.drawEllipse(QPointF(8, 15.5), 0.9, 0.9)


def _paint_cloud(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(7, 15)
    path.cubicTo(4.5, 15, 4.5, 11, 7.5, 10.5)
    path.cubicTo(8, 7.5, 14, 7, 15, 10)
    path.cubicTo(18.5, 10, 19, 15, 15.5, 15)
    path.closeSubpath()
    p.drawPath(path)


def _paint_vpn(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(12, 12), 6.5, 6.5)
    p.drawLine(QPointF(12, 8), QPointF(12, 12))
    p.drawLine(QPointF(12, 12), QPointF(15, 14.5))


def _paint_ssh(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(4.5, 6, 15, 12), 2, 2)
    path = QPainterPath()
    path.moveTo(7.5, 10)
    path.lineTo(10, 12)
    path.lineTo(7.5, 14)
    p.drawPath(path)
    p.drawLine(QPointF(11.5, 14), QPointF(16, 14))


def _paint_docker(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_fg())
    for x in (6, 9.2, 12.4):
        p.drawRoundedRect(QRectF(x, 11, 2.8, 2.8), 0.4, 0.4)
    p.drawRoundedRect(QRectF(9.2, 7.5, 2.8, 2.8), 0.4, 0.4)
    p.setPen(_pen(_fg(), 1.3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(5, 15)
    path.cubicTo(5, 18, 19, 18, 19, 14)
    p.drawPath(path)


def _paint_k8s(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.4))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(12, 12), 2.2, 2.2)
    for angle in (0, 60, 120, 180, 240, 300):
        import math

        rad = math.radians(angle - 90)
        x = 12 + 6 * math.cos(rad)
        y = 12 + 6 * math.sin(rad)
        p.drawEllipse(QPointF(x, y), 1.3, 1.3)
        p.drawLine(QPointF(12, 12), QPointF(x, y))


def _paint_database(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.4))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(12, 7.5), 5.5, 2.2)
    path = QPainterPath()
    path.moveTo(6.5, 7.5)
    path.lineTo(6.5, 12)
    path.cubicTo(6.5, 14, 17.5, 14, 17.5, 12)
    path.lineTo(17.5, 7.5)
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(6.5, 12)
    path2.lineTo(6.5, 16.5)
    path2.cubicTo(6.5, 18.5, 17.5, 18.5, 17.5, 16.5)
    path2.lineTo(17.5, 12)
    p.drawPath(path2)


def _paint_email(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(5, 7, 14, 10), 1.5, 1.5)
    path = QPainterPath()
    path.moveTo(5, 8.5)
    path.lineTo(12, 13.5)
    path.lineTo(19, 8.5)
    p.drawPath(path)


def _paint_bank(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.4))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(5, 10)
    path.lineTo(12, 6)
    path.lineTo(19, 10)
    path.closeSubpath()
    p.drawPath(path)
    for x in (7, 10, 13, 16):
        p.drawLine(QPointF(x, 10), QPointF(x, 16))
    p.drawLine(QPointF(5, 16.5), QPointF(19, 16.5))


def _paint_wifi(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(6, 10)
    path.cubicTo(8.5, 7.5, 15.5, 7.5, 18, 10)
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(8, 12.5)
    path2.cubicTo(9.5, 11, 14.5, 11, 16, 12.5)
    p.drawPath(path2)
    p.setBrush(_fg())
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(12, 16), 1.3, 1.3)


def _paint_crypto(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(10, 6), QPointF(10, 18))
    p.drawLine(QPointF(13, 6), QPointF(13, 18))
    path = QPainterPath()
    path.moveTo(10, 8)
    path.lineTo(14.5, 8)
    path.cubicTo(16.5, 8, 16.5, 12, 14.5, 12)
    path.lineTo(10, 12)
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(10, 12)
    path2.lineTo(15, 12)
    path2.cubicTo(17, 12, 17, 16.5, 15, 16.5)
    path2.lineTo(10, 16.5)
    p.drawPath(path2)


def _paint_identity(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(6, 5, 12, 14), 2, 2)
    p.drawEllipse(QPointF(12, 9.5), 2.3, 2.3)
    path = QPainterPath()
    path.moveTo(8.5, 15.5)
    path.cubicTo(8.5, 13.5, 15.5, 13.5, 15.5, 15.5)
    p.drawPath(path)


def _paint_api(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(9, 8)
    path.lineTo(5.5, 12)
    path.lineTo(9, 16)
    path.moveTo(15, 8)
    path.lineTo(18.5, 12)
    path.lineTo(15, 16)
    p.drawPath(path)


def _paint_certificate(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(12, 5)
    path.lineTo(18, 7.5)
    path.lineTo(18, 12)
    path.cubicTo(18, 16, 14.5, 18.5, 12, 19.5)
    path.cubicTo(9.5, 18.5, 6, 16, 6, 12)
    path.lineTo(6, 7.5)
    path.closeSubpath()
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(9.5, 12)
    path2.lineTo(11.2, 13.7)
    path2.lineTo(14.8, 10)
    p.drawPath(path2)


def _paint_dev(p: QPainter, c: QColor) -> None:
    _paint_api(p, c)


def _paint_note(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(7, 5)
    path.lineTo(13, 5)
    path.lineTo(17, 9)
    path.lineTo(17, 19)
    path.lineTo(7, 19)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(QPointF(13, 5), QPointF(13, 9))
    p.drawLine(QPointF(13, 9), QPointF(17, 9))
    p.drawLine(QPointF(9, 12), QPointF(15, 12))
    p.drawLine(QPointF(9, 15), QPointF(15, 15))


def _paint_license(p: QPainter, c: QColor) -> None:
    _paint_certificate(p, c)


def _paint_recycle(p: QPainter, c: QColor) -> None:
    _badge(p, c)
    p.setPen(_pen(_fg(), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(6, 8), QPointF(18, 8))
    p.drawLine(QPointF(9, 8), QPointF(9, 6.5))
    p.drawLine(QPointF(15, 8), QPointF(15, 6.5))
    p.drawLine(QPointF(9, 6.5), QPointF(15, 6.5))
    path = QPainterPath()
    path.moveTo(8, 8)
    path.lineTo(9, 18)
    path.lineTo(15, 18)
    path.lineTo(16, 8)
    p.drawPath(path)


_PAINTERS: dict[GroupKind, Callable[[QPainter, QColor], None]] = {
    GroupKind.HOME: _paint_home,
    GroupKind.FOLDER: _paint_folder,
    GroupKind.INTERNET: _paint_internet,
    GroupKind.WINDOWS: _paint_windows,
    GroupKind.LINUX: _paint_linux,
    GroupKind.MACOS: _paint_macos,
    GroupKind.SERVER: _paint_server,
    GroupKind.CLOUD: _paint_cloud,
    GroupKind.VPN: _paint_vpn,
    GroupKind.SSH: _paint_ssh,
    GroupKind.DOCKER: _paint_docker,
    GroupKind.KUBERNETES: _paint_k8s,
    GroupKind.DATABASE: _paint_database,
    GroupKind.EMAIL: _paint_email,
    GroupKind.BANK: _paint_bank,
    GroupKind.WIFI: _paint_wifi,
    GroupKind.CRYPTO: _paint_crypto,
    GroupKind.IDENTITY: _paint_identity,
    GroupKind.API: _paint_api,
    GroupKind.CERTIFICATE: _paint_certificate,
    GroupKind.DEV: _paint_dev,
    GroupKind.NOTE: _paint_note,
    GroupKind.LICENSE: _paint_license,
    GroupKind.RECYCLE: _paint_recycle,
}


@lru_cache(maxsize=128)
def _pixmap_for(kind: str, size: int) -> QPixmap:
    group_kind = GroupKind(kind)
    painter_fn = _PAINTERS.get(group_kind, _paint_folder)
    color = QColor(group_kind_color(group_kind))
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scale = size / 24.0
    painter.scale(scale, scale)
    painter_fn(painter, color)
    painter.end()
    return pm


def clear_group_icon_cache() -> None:
    _pixmap_for.cache_clear()


def group_kind_icon(kind: GroupKind, *, size: int = 18) -> QIcon:
    return QIcon(_pixmap_for(kind.value, size))


def group_icon_for_name(
    name: str,
    *,
    is_recycle_bin: bool = False,
    size: int = 18,
) -> QIcon:
    """Resolve a colorful category icon from a group name."""
    kind = detect_group_kind(name, is_recycle_bin=is_recycle_bin)
    return group_kind_icon(kind, size=size)
