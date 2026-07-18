"""Simple plugin list dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QWidget,
)

from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.i18n import tr
from kdbxstudio.ui.widgets.dialog_shell import DialogShell


class PluginDialog(DialogShell):
    def __init__(
        self, manager: PluginManager, parent: QWidget | None = None
    ) -> None:
        super().__init__(
            parent,
            title=tr("Plugins"),
            subtitle=tr("Activate or deactivate installed plugins"),
            icon_name="extension",
            width=520,
        )
        self._manager = manager
        self.resize(520, 360)

        self._list = QListWidget()
        activate = QPushButton(tr("Activate"))
        deactivate = QPushButton(tr("Deactivate"))
        activate.clicked.connect(self._activate)
        deactivate.clicked.connect(self._deactivate)

        buttons = QHBoxLayout()
        buttons.addWidget(activate)
        buttons.addWidget(deactivate)
        buttons.addStretch()
        self.body.addWidget(self._list)
        self.body.addLayout(buttons)

        self.button_box.clear()
        close = self.button_box.addButton(QDialogButtonBox.StandardButton.Close)
        if close is not None:
            close.setProperty("cssClass", "primary")
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)
        self._reload()

    def _reload(self) -> None:
        self._list.clear()
        for info in self._manager.list_plugins():
            state = "active" if info.active else "inactive"
            text = f"{info.name} {info.version} [{state}] — {info.description}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, info.name)
            self._list.addItem(item)

    def _selected_name(self) -> str | None:
        item = self._list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def _activate(self) -> None:
        name = self._selected_name()
        if name:
            self._manager.activate(name)
            self._reload()

    def _deactivate(self) -> None:
        name = self._selected_name()
        if name:
            self._manager.deactivate(name)
            self._reload()
