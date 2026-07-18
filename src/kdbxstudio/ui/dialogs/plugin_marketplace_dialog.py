"""Plugin Marketplace dialog."""

from __future__ import annotations

import importlib

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QWidget,
)

from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.i18n import tr
from kdbxstudio.plugins.marketplace import MarketplacePlugin, get_catalog
from kdbxstudio.ui.widgets.dialog_shell import DialogShell


class PluginMarketplaceDialog(DialogShell):
    def __init__(
        self,
        manager: PluginManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
            title=tr("Plugin Marketplace"),
            subtitle=tr("Browse and install catalog plugins"),
            icon_name="extension",
            width=680,
        )
        self.resize(680, 460)
        self._manager = manager
        self._catalog = get_catalog()

        self._list = QListWidget()
        self._list.setAccessibleName(tr("Plugin catalog"))
        self._list.currentRowChanged.connect(self._on_select)
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setAccessibleName(tr("Plugin details"))
        self._status = QLabel("")
        self._status.setAccessibleName(tr("Marketplace status"))

        install = QPushButton(tr("Install / Register"))
        install.clicked.connect(self._install)
        activate = QPushButton(tr("Activate"))
        activate.clicked.connect(self._activate)
        deactivate = QPushButton(tr("Deactivate"))
        deactivate.clicked.connect(self._deactivate)

        actions = QHBoxLayout()
        actions.addWidget(install)
        actions.addWidget(activate)
        actions.addWidget(deactivate)
        actions.addStretch()

        self.body.addWidget(self._list, stretch=1)
        self.body.addWidget(self._detail, stretch=1)
        self.body.addWidget(self._status)
        self.body.addLayout(actions)

        self.button_box.clear()
        close = self.button_box.addButton(QDialogButtonBox.StandardButton.Close)
        if close is not None:
            close.setProperty("cssClass", "primary")
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)

        for plugin in self._catalog:
            item = QListWidgetItem(f"{plugin.name} — {plugin.summary}")
            item.setData(Qt.ItemDataRole.UserRole, plugin.id)
            self._list.addItem(item)
        if self._catalog:
            self._list.setCurrentRow(0)

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
