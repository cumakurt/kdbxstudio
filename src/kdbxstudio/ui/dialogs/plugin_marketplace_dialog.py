"""Plugin Marketplace dialog."""

from __future__ import annotations

import importlib

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.plugins.marketplace import MarketplacePlugin, get_catalog


class PluginMarketplaceDialog(QDialog):
    def __init__(
        self,
        manager: PluginManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Plugin Marketplace")
        self.setModal(True)
        self.resize(640, 420)
        self._manager = manager
        self._catalog = get_catalog()

        self._list = QListWidget()
        self._list.setAccessibleName("Plugin catalog")
        self._list.currentRowChanged.connect(self._on_select)
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setAccessibleName("Plugin details")
        self._status = QLabel("")
        self._status.setAccessibleName("Marketplace status")

        install = QPushButton("Install / Register")
        install.clicked.connect(self._install)
        activate = QPushButton("Activate")
        activate.clicked.connect(self._activate)
        deactivate = QPushButton("Deactivate")
        deactivate.clicked.connect(self._deactivate)

        buttons = QHBoxLayout()
        buttons.addWidget(install)
        buttons.addWidget(activate)
        buttons.addWidget(deactivate)
        buttons.addStretch()

        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        close.accepted.connect(self.accept)

        body = QHBoxLayout()
        body.addWidget(self._list, 2)
        body.addWidget(self._detail, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Browse built-in and local plugins"))
        layout.addLayout(body)
        layout.addLayout(buttons)
        layout.addWidget(self._status)
        layout.addWidget(close)
        self._reload()

    def _reload(self) -> None:
        self._list.clear()
        active = {p.name for p in self._manager.list_plugins() if p.active}
        registered = {p.name for p in self._manager.list_plugins()}
        for item in self._catalog:
            state = []
            if item.id in registered:
                state.append("installed")
            if item.id in active:
                state.append("active")
            suffix = f" [{', '.join(state)}]" if state else ""
            row = QListWidgetItem(f"{item.name} {item.version}{suffix}")
            row.setData(Qt.ItemDataRole.UserRole, item.id)
            self._list.addItem(row)
        if self._catalog:
            self._list.setCurrentRow(0)

    def _current(self) -> MarketplacePlugin | None:
        item = self._list.currentItem()
        if item is None:
            return None
        plugin_id = str(item.data(Qt.ItemDataRole.UserRole))
        for entry in self._catalog:
            if entry.id == plugin_id:
                return entry
        return None

    def _on_select(self, _row: int) -> None:
        entry = self._current()
        if entry is None:
            self._detail.clear()
            return
        self._detail.setPlainText(
            "\n".join(
                [
                    f"Name: {entry.name}",
                    f"ID: {entry.id}",
                    f"Version: {entry.version}",
                    f"Author: {entry.author}",
                    f"Built-in: {'yes' if entry.builtin else 'no'}",
                    "",
                    entry.description,
                ]
            )
        )

    def _install(self) -> None:
        entry = self._current()
        if entry is None or not entry.module:
            return
        try:
            module = importlib.import_module(entry.module)
            factory = getattr(module, "create_plugin", None)
            if factory is None:
                raise RuntimeError("create_plugin() missing")
            plugin = factory()
            self._manager.register(plugin)
            self._status.setText(f"Registered {entry.name}")
            self._reload()
        except Exception as exc:
            QMessageBox.critical(self, "Install failed", str(exc))

    def _activate(self) -> None:
        entry = self._current()
        if entry is None:
            return
        try:
            if entry.id not in {p.name for p in self._manager.list_plugins()}:
                self._install()
                if entry.id not in {p.name for p in self._manager.list_plugins()}:
                    return
            self._manager.activate(entry.id)
            self._status.setText(f"Activated {entry.name}")
            self._reload()
        except Exception as exc:
            QMessageBox.critical(self, "Activate failed", str(exc))

    def _deactivate(self) -> None:
        entry = self._current()
        if entry is None:
            return
        try:
            self._manager.deactivate(entry.id)
            self._status.setText(f"Deactivated {entry.name}")
            self._reload()
        except Exception as exc:
            QMessageBox.critical(self, "Deactivate failed", str(exc))
