"""Simple plugin list dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.application.plugin_manager import PluginManager


class PluginDialog(QDialog):
    def __init__(
        self, manager: PluginManager, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Plugins")
        self._manager = manager
        self.resize(480, 320)

        self._list = QListWidget()
        activate = QPushButton("Activate")
        deactivate = QPushButton("Deactivate")
        activate.clicked.connect(self._activate)
        deactivate.clicked.connect(self._deactivate)

        buttons = QHBoxLayout()
        buttons.addWidget(activate)
        buttons.addWidget(deactivate)
        buttons.addStretch()

        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        close.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        layout.addLayout(buttons)
        layout.addWidget(close)
        self._reload()

    def _reload(self) -> None:
        self._list.clear()
        for info in self._manager.list_plugins():
            state = "active" if info.active else "inactive"
            text = f"{info.name} {info.version} [{state}] — {info.description}"
            item = QListWidgetItem(text)
            item.setData(256, info.name)
            self._list.addItem(item)

    def _selected_name(self) -> str | None:
        item = self._list.currentItem()
        if item is None:
            return None
        value = item.data(256)
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
