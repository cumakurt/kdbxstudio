"""Tinted Material-style icons painted with QPainter (no QtSvg dependency)."""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QStyle, QToolButton, QWidget

from kdbxstudio.ui.theme.manager import current_tokens

# Public name constants (stable API)
ICON_OPEN = "folder_open"
ICON_SAVE = "save"
ICON_ADD = "add"
ICON_LOCK = "lock"
ICON_SEARCH = "search"
ICON_AUDIT = "health_and_safety"
ICON_PALETTE = "palette"
ICON_SETTINGS = "settings"
ICON_KEY = "key"
ICON_PLUGIN = "extension"
ICON_THEME = "contrast"
ICON_DASHBOARD = "dashboard"
ICON_DELETE = "delete"
ICON_COPY = "content_copy"
ICON_EDIT = "edit"
ICON_CLOSE = "close"
ICON_INFO = "info"

_FALLBACK_SP: dict[str, QStyle.StandardPixmap] = {
    ICON_OPEN: QStyle.StandardPixmap.SP_DirOpenIcon,
    ICON_SAVE: QStyle.StandardPixmap.SP_DialogSaveButton,
    ICON_ADD: QStyle.StandardPixmap.SP_FileDialogNewFolder,
    ICON_LOCK: QStyle.StandardPixmap.SP_DialogNoButton,
    ICON_SEARCH: QStyle.StandardPixmap.SP_FileDialogContentsView,
    ICON_AUDIT: QStyle.StandardPixmap.SP_MessageBoxInformation,
    ICON_PALETTE: QStyle.StandardPixmap.SP_TitleBarMenuButton,
    ICON_SETTINGS: QStyle.StandardPixmap.SP_FileDialogDetailedView,
    ICON_KEY: QStyle.StandardPixmap.SP_DialogApplyButton,
    ICON_PLUGIN: QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton,
    ICON_THEME: QStyle.StandardPixmap.SP_DesktopIcon,
}

# Icon names that have custom painters (24×24 logical space).
IconPainter = Callable[[QPainter, QColor], None]
_PAINTERS: dict[str, IconPainter] = {}


def _reg(name: str) -> Callable[[IconPainter], IconPainter]:
    def deco(fn: IconPainter) -> IconPainter:
        _PAINTERS[name] = fn
        return fn

    return deco


def _pen(color: QColor, width: float = 1.75) -> QPen:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _line(p: QPainter, x1: float, y1: float, x2: float, y2: float) -> None:
    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


@_reg("folder_open")
def _folder_open(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.addRoundedRect(QRectF(3, 8, 18, 11), 1.5, 1.5)
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(3, 10)
    path2.lineTo(9, 10)
    path2.lineTo(11, 7)
    path2.lineTo(4.5, 7)
    path2.closeSubpath()
    p.drawPath(path2)


@_reg("folder")
def _folder(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(3, 8)
    path.lineTo(9, 8)
    path.lineTo(11, 6)
    path.lineTo(20, 6)
    path.lineTo(20, 18)
    path.lineTo(3, 18)
    path.closeSubpath()
    p.drawPath(path)


@_reg("save")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(5, 4)
    path.lineTo(16, 4)
    path.lineTo(19, 7)
    path.lineTo(19, 20)
    path.lineTo(5, 20)
    path.closeSubpath()
    p.drawPath(path)
    p.drawRect(QRectF(8, 4, 8, 5))
    _line(p, 8, 15, 16, 15)


@_reg("add")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    _line(p, 12, 5, 12, 19)
    _line(p, 5, 12, 19, 12)


@_reg("lock")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(5, 11, 14, 10), 2, 2)
    path = QPainterPath()
    path.moveTo(8, 11)
    path.cubicTo(8, 6, 16, 6, 16, 11)
    p.drawPath(path)


@_reg("search")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(11, 11), 6, 6)
    _line(p, 16, 16, 20, 20)


@_reg("health_and_safety")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(12, 3)
    path.lineTo(20, 6)
    path.lineTo(20, 12)
    path.cubicTo(20, 17, 16, 20, 12, 21.5)
    path.cubicTo(8, 20, 4, 17, 4, 12)
    path.lineTo(4, 6)
    path.closeSubpath()
    p.drawPath(path)
    _line(p, 12, 8, 12, 16)
    _line(p, 8, 12, 16, 12)


@_reg("terminal")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3, 5, 18, 14), 2, 2)
    path = QPainterPath()
    path.moveTo(7, 10)
    path.lineTo(10, 12)
    path.lineTo(7, 14)
    p.drawPath(path)
    _line(p, 12, 14, 17, 14)


@_reg("settings")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(12, 12), 3, 3)
    for angle in range(0, 360, 45):
        import math

        rad = math.radians(angle)
        x1, y1 = 12 + 6.5 * math.cos(rad), 12 + 6.5 * math.sin(rad)
        x2, y2 = 12 + 9 * math.cos(rad), 12 + 9 * math.sin(rad)
        _line(p, x1, y1, x2, y2)


@_reg("key")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(8, 14), 3.5, 3.5)
    _line(p, 11, 12.5, 20, 8.5)
    _line(p, 20, 8.5, 20, 11.5)
    _line(p, 17, 10, 17, 13)


@_reg("extension")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(7, 4, 4, 4), 1, 1)
    p.drawRoundedRect(QRectF(7, 10, 10, 4), 1, 1)
    p.drawRoundedRect(QRectF(13, 7, 4, 4), 1, 1)
    p.drawRoundedRect(QRectF(7, 14, 4, 6), 1, 1)


@_reg("contrast")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(12, 12), 8, 8)
    path = QPainterPath()
    path.moveTo(12, 4)
    path.arcTo(QRectF(4, 4, 16, 16), 90, 180)
    path.closeSubpath()
    p.setBrush(c)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(path)


@_reg("palette")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.addEllipse(QPointF(12, 12), 8, 8)
    p.drawPath(path)
    for cx, cy in ((8, 10), (11, 7.5), (15, 8), (16.5, 11.5)):
        p.drawEllipse(QPointF(cx, cy), 1, 1)


@_reg("note_add")
@_reg("article")
@_reg("description")
@_reg("sticky_note")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(7, 3)
    path.lineTo(14, 3)
    path.lineTo(18, 7)
    path.lineTo(18, 21)
    path.lineTo(7, 21)
    path.closeSubpath()
    p.drawPath(path)
    _line(p, 14, 3, 14, 7)
    _line(p, 14, 7, 18, 7)
    _line(p, 9, 12, 15, 12)
    _line(p, 9, 16, 15, 16)


@_reg("close")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    _line(p, 6, 6, 18, 18)
    _line(p, 18, 6, 6, 18)


@_reg("logout")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(4, 5, 8, 14), 2, 2)
    _line(p, 14, 12, 7, 12)
    path = QPainterPath()
    path.moveTo(14, 12)
    path.lineTo(17, 9)
    path.moveTo(14, 12)
    path.lineTo(17, 15)
    p.drawPath(path)


@_reg("history")
@_reg("refresh")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.arcMoveTo(QRectF(4, 4, 16, 16), 40)
    path.arcTo(QRectF(4, 4, 16, 16), 40, 280)
    p.drawPath(path)
    _line(p, 18, 5, 18, 10)
    _line(p, 18, 10, 13, 10)


@_reg("info")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(12, 12), 8, 8)
    _line(p, 12, 11, 12, 16)
    p.drawEllipse(QPointF(12, 8), 0.8, 0.8)


@_reg("upload")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    _line(p, 12, 16, 12, 5)
    path = QPainterPath()
    path.moveTo(8, 9)
    path.lineTo(12, 5)
    path.lineTo(16, 9)
    p.drawPath(path)
    _line(p, 5, 19, 19, 19)


@_reg("download")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    _line(p, 12, 5, 12, 16)
    path = QPainterPath()
    path.moveTo(8, 12)
    path.lineTo(12, 16)
    path.lineTo(16, 12)
    p.drawPath(path)
    _line(p, 5, 19, 19, 19)


@_reg("person_add")
@_reg("person")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(10, 8), 3, 3)
    path = QPainterPath()
    path.moveTo(4, 19)
    path.cubicTo(4, 14, 16, 14, 16, 19)
    p.drawPath(path)
    _line(p, 18, 8, 18, 14)
    _line(p, 15, 11, 21, 11)


@_reg("delete")
@_reg("delete_sweep")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    _line(p, 5, 7, 19, 7)
    _line(p, 9, 7, 9, 5)
    _line(p, 15, 7, 15, 5)
    _line(p, 9, 5, 15, 5)
    path = QPainterPath()
    path.moveTo(8, 7)
    path.lineTo(9, 19)
    path.lineTo(15, 19)
    path.lineTo(16, 7)
    p.drawPath(path)


@_reg("drive_file_move")
def _(p: QPainter, c: QColor) -> None:
    _folder(p, c)
    _line(p, 10, 14, 15, 14)
    path = QPainterPath()
    path.moveTo(13, 11)
    path.lineTo(16, 14)
    path.lineTo(13, 17)
    p.drawPath(path)


@_reg("edit")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(4, 20)
    path.lineTo(8, 20)
    path.lineTo(18, 10)
    path.lineTo(14, 6)
    path.lineTo(4, 16)
    path.closeSubpath()
    p.drawPath(path)


@_reg("content_copy")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(8, 8, 11, 12), 1.5, 1.5)
    path = QPainterPath()
    path.moveTo(5, 16)
    path.lineTo(5, 5.5)
    path.lineTo(15, 5.5)
    p.drawPath(path)


@_reg("dashboard")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3, 3, 8, 8), 1.5, 1.5)
    p.drawRoundedRect(QRectF(13, 3, 8, 5), 1.5, 1.5)
    p.drawRoundedRect(QRectF(13, 10, 8, 11), 1.5, 1.5)
    p.drawRoundedRect(QRectF(3, 13, 8, 8), 1.5, 1.5)


@_reg("password")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3, 8, 18, 10), 2, 2)
    for x in (8, 12, 16):
        p.drawEllipse(QPointF(x, 13), 1.2, 1.2)


@_reg("merge")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(7, 4), 1.5, 1.5)
    p.drawEllipse(QPointF(17, 4), 1.5, 1.5)
    p.drawEllipse(QPointF(7, 20), 1.5, 1.5)
    p.drawEllipse(QPointF(17, 20), 1.5, 1.5)
    _line(p, 7, 5.5, 7, 12)
    _line(p, 17, 5.5, 17, 12)
    path = QPainterPath()
    path.moveTo(7, 12)
    path.cubicTo(7, 16, 17, 16, 17, 12)
    p.drawPath(path)
    _line(p, 7, 16, 7, 18.5)
    _line(p, 17, 16, 17, 18.5)


@_reg("system_update")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(6, 3, 12, 18), 2, 2)
    _line(p, 12, 8, 12, 14)
    path = QPainterPath()
    path.moveTo(9, 11)
    path.lineTo(12, 14)
    path.lineTo(15, 11)
    p.drawPath(path)


@_reg("vpn_key")
@_reg("vpn_lock")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(12, 12), 8, 8)
    _line(p, 12, 8, 12, 12)
    _line(p, 12, 12, 14.5, 14.5)


@_reg("link")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(9, 12)
    path.cubicTo(9, 8, 15, 8, 15, 12)
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(9, 12)
    path2.cubicTo(9, 16, 15, 16, 15, 12)
    p.drawPath(path2)


@_reg("pin")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(8, 4)
    path.lineTo(16, 4)
    path.lineTo(15, 10)
    path.lineTo(18, 10)
    path.lineTo(12, 15)
    path.lineTo(6, 10)
    path.lineTo(9, 10)
    path.closeSubpath()
    p.drawPath(path)
    _line(p, 12, 15, 12, 20)


@_reg("visibility")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(2, 12)
    path.cubicTo(6, 6, 18, 6, 22, 12)
    path.cubicTo(18, 18, 6, 18, 2, 12)
    p.drawPath(path)
    p.drawEllipse(QPointF(12, 12), 2.5, 2.5)


@_reg("visibility_off")
def _(p: QPainter, c: QColor) -> None:
    _visibility = _PAINTERS.get("visibility")
    if callable(_visibility):
        _visibility(p, c)
    _line(p, 4, 4, 20, 20)


@_reg("language")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(12, 12), 8, 8)
    _line(p, 4, 12, 20, 12)
    path = QPainterPath()
    path.moveTo(12, 4)
    path.cubicTo(16, 8, 16, 16, 12, 20)
    path.moveTo(12, 4)
    path.cubicTo(8, 8, 8, 16, 12, 20)
    p.drawPath(path)


@_reg("dns")
@_reg("computer")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3, 5, 18, 12), 2, 2)
    _line(p, 8, 21, 16, 21)
    _line(p, 12, 17, 12, 21)


@_reg("window")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3, 4, 18, 16), 2, 2)
    _line(p, 3, 9, 21, 9)


@_reg("cloud")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(7.5, 18)
    path.lineTo(17.5, 18)
    path.cubicTo(21, 18, 21, 12, 17, 11)
    path.cubicTo(17, 7, 12, 5, 9, 8)
    path.cubicTo(5, 8, 4, 12, 7.5, 14)
    path.closeSubpath()
    p.drawPath(path)


@_reg("verified_user")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(12, 3)
    path.lineTo(20, 6)
    path.lineTo(20, 11)
    path.cubicTo(20, 16, 16, 19.5, 12, 21)
    path.cubicTo(8, 19.5, 4, 16, 4, 11)
    path.lineTo(4, 6)
    path.closeSubpath()
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(9, 12)
    path2.lineTo(11, 14)
    path2.lineTo(15, 10)
    p.drawPath(path2)


@_reg("deployed_code")
@_reg("hub")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(12, 3)
    path.lineTo(20, 7)
    path.lineTo(20, 17)
    path.lineTo(12, 21)
    path.lineTo(4, 17)
    path.lineTo(4, 7)
    path.closeSubpath()
    p.drawPath(path)
    _line(p, 12, 12, 20, 7)
    _line(p, 12, 12, 4, 7)
    _line(p, 12, 12, 12, 21)


@_reg("api")
@_reg("code")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(8, 8)
    path.lineTo(4, 12)
    path.lineTo(8, 16)
    path.moveTo(16, 8)
    path.lineTo(20, 12)
    path.lineTo(16, 16)
    p.drawPath(path)


@_reg("database")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(12, 6), 7, 3)
    path = QPainterPath()
    path.moveTo(5, 6)
    path.lineTo(5, 12)
    path.cubicTo(5, 14.5, 19, 14.5, 19, 12)
    path.lineTo(19, 6)
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(5, 12)
    path2.lineTo(5, 18)
    path2.cubicTo(5, 20.5, 19, 20.5, 19, 18)
    path2.lineTo(19, 12)
    p.drawPath(path2)


@_reg("wifi")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(5, 10.5)
    path.cubicTo(8, 7, 16, 7, 19, 10.5)
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(8, 13.5)
    path2.cubicTo(10, 11.5, 14, 11.5, 16, 13.5)
    p.drawPath(path2)
    p.drawEllipse(QPointF(12, 17), 1.2, 1.2)


@_reg("badge")
@_reg("mail")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3, 6, 18, 12), 2, 2)
    path = QPainterPath()
    path.moveTo(3, 8)
    path.lineTo(12, 14)
    path.lineTo(21, 8)
    p.drawPath(path)


@_reg("account_balance")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(3, 10)
    path.lineTo(12, 4)
    path.lineTo(21, 10)
    path.closeSubpath()
    p.drawPath(path)
    for x in (6, 10, 14, 18):
        _line(p, x, 10, x, 18)
    _line(p, 3, 18, 21, 18)
    _line(p, 4, 10, 20, 10)


@_reg("currency_bitcoin")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    _line(p, 9, 6, 9, 18)
    _line(p, 12, 6, 12, 18)
    path = QPainterPath()
    path.moveTo(9, 8)
    path.lineTo(14, 8)
    path.cubicTo(16.5, 8, 16.5, 13, 14, 13)
    path.lineTo(9, 13)
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(9, 13)
    path2.lineTo(15, 13)
    path2.cubicTo(17.5, 13, 17.5, 18, 15, 18)
    path2.lineTo(9, 18)
    p.drawPath(path2)


@_reg("license")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(7, 3)
    path.lineTo(14, 3)
    path.lineTo(18, 7)
    path.lineTo(18, 21)
    path.lineTo(7, 21)
    path.closeSubpath()
    p.drawPath(path)
    path2 = QPainterPath()
    path2.moveTo(9, 13)
    path2.lineTo(11, 15)
    path2.lineTo(15, 11)
    p.drawPath(path2)


@_reg("attach_file")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(15, 7)
    path.lineTo(15, 15.5)
    path.cubicTo(15, 18.5, 8, 18.5, 8, 15.5)
    path.lineTo(8, 6)
    path.cubicTo(8, 3.5, 13, 3.5, 13, 6)
    path.lineTo(13, 14.5)
    path.cubicTo(13, 16, 10, 16, 10, 14.5)
    path.lineTo(10, 8)
    p.drawPath(path)


@_reg("check")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(5, 12)
    path.lineTo(10, 17)
    path.lineTo(19, 8)
    p.drawPath(path)


@_reg("chevron_right")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(9, 6)
    path.lineTo(15, 12)
    path.lineTo(9, 18)
    p.drawPath(path)


@_reg("expand_more")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    path = QPainterPath()
    path.moveTo(6, 9)
    path.lineTo(12, 15)
    path.lineTo(18, 9)
    p.drawPath(path)


@_reg("auto_fix_fill")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(4, 6, 16, 4), 1, 1)
    p.drawRoundedRect(QRectF(4, 14, 10, 4), 1, 1)
    path = QPainterPath()
    path.moveTo(16, 15)
    path.lineTo(19, 17)
    path.lineTo(16, 19)
    p.drawPath(path)


@_reg("image")
def _(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3, 5, 18, 14), 2, 2)
    p.drawEllipse(QPointF(9, 10), 1.5, 1.5)
    path = QPainterPath()
    path.moveTo(4, 17)
    path.lineTo(9, 12)
    path.lineTo(12, 15)
    path.lineTo(15, 12)
    path.lineTo(20, 17)
    p.drawPath(path)


def known_icons() -> frozenset[str]:
    return frozenset(_PAINTERS)


def _default_color() -> str:
    try:
        return current_tokens().text_primary
    except Exception:
        return "#E8F0F0"


def _brand_color() -> str:
    try:
        return current_tokens().brand_primary
    except Exception:
        return "#3D9A9C"


@lru_cache(maxsize=256)
def _pixmap_for(name: str, color: str, size: int) -> QPixmap:
    painter_fn = _PAINTERS.get(name)
    if painter_fn is None:
        return QPixmap()
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scale = size / 24.0
    painter.scale(scale, scale)
    painter_fn(painter, QColor(color))
    painter.end()
    return pm


def clear_icon_cache() -> None:
    _pixmap_for.cache_clear()


def icon(
    name: str,
    *,
    size: int = 20,
    color: str | None = None,
    brand: bool = False,
) -> QIcon:
    """Return a tinted outlined icon; falls back to Qt SP_* if glyph missing."""
    tint = color or (_brand_color() if brand else _default_color())
    if name in _PAINTERS:
        pm = _pixmap_for(name, tint, size)
        if not pm.isNull():
            return QIcon(pm)
    return _fallback_icon(name)


def _fallback_icon(name: str) -> QIcon:
    pixmap = _FALLBACK_SP.get(name, QStyle.StandardPixmap.SP_FileIcon)
    app = QApplication.instance()
    if isinstance(app, QApplication):
        style = app.style()
        if style is not None:
            return style.standardIcon(pixmap)
    return QIcon()


def standard_icon(name: str) -> QIcon:
    return icon(name)


def menu_icon(name: str, size: int = 18) -> QIcon:
    return icon(name, size=size)


def icon_label(name: str, parent: QWidget | None = None, size: int = 16) -> QLabel:
    label = QLabel(parent)
    label.setPixmap(icon(name, size=size).pixmap(size, size))
    label.setAccessibleName(name.replace("_", " "))
    return label


def icon_tool_button(
    name: str,
    tooltip: str,
    parent: QWidget | None = None,
    size: int = 20,
) -> QToolButton:
    button = QToolButton(parent)
    button.setIcon(icon(name, size=size))
    button.setIconSize(QSize(size, size))
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    button.setText("")
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
    button.setAutoRaise(True)
    button.setFixedSize(size + 12, size + 12)
    return button
