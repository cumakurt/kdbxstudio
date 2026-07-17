"""Toolbar and UI icon helpers using Qt standard icons."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QStyle,
    QToolButton,
    QWidget,
)

ICON_OPEN = "folder_open"
ICON_SAVE = "save"
ICON_ADD = "add"
ICON_LOCK = "lock"
ICON_SEARCH = "search"
ICON_AUDIT = "health_and_safety"
ICON_PALETTE = "terminal"
ICON_SETTINGS = "settings"
ICON_KEY = "key"
ICON_PLUGIN = "extension"
ICON_THEME = "contrast"

_STYLE_ICONS: dict[str, QStyle.StandardPixmap] = {
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


def standard_icon(name: str) -> QIcon:
    pixmap = _STYLE_ICONS.get(name, QStyle.StandardPixmap.SP_FileIcon)
    app = QApplication.instance()
    if isinstance(app, QApplication):
        style = app.style()
        if style is not None:
            return style.standardIcon(pixmap)
    return QIcon()


def icon_label(name: str, parent: QWidget | None = None, size: int = 16) -> QLabel:
    label = QLabel(parent)
    label.setPixmap(standard_icon(name).pixmap(size, size))
    label.setAccessibleName(name.replace("_", " "))
    return label


def icon_tool_button(
    name: str,
    tooltip: str,
    parent: QWidget | None = None,
    size: int = 16,
) -> QToolButton:
    button = QToolButton(parent)
    button.setIcon(standard_icon(name))
    button.setIconSize(QSize(size, size))
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    button.setText("")
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
    button.setAutoRaise(True)
    button.setFixedSize(size + 8, size + 8)
    return button
