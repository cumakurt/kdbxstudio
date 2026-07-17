"""Entry list widget with per-entry type icons and optional favicons."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
)

from kdbxstudio.application.favicon import cached_favicon
from kdbxstudio.core.database import EntryView
from kdbxstudio.ui.icons.entry_type import detect_entry_kind_from_view, entry_kind_icon


class EntryListWidget(QTableWidget):
    """Shows entries for the selected group."""

    entry_selected = Signal(str)

    COLUMNS = ("Title", "Username", "URL")

    def __init__(self, parent: QTableWidget | None = None) -> None:
        super().__init__(0, len(self.COLUMNS), parent)
        self.setHorizontalHeaderLabels(list(self.COLUMNS))
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setIconSize(QSize(16, 16))
        self.itemSelectionChanged.connect(self._on_selection)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.horizontalHeader().sectionClicked.connect(self._on_sort)

    def set_entries(self, entries: list[EntryView]) -> None:
        self.setRowCount(0)
        self.setSortingEnabled(False)
        for entry in entries:
            row = self.rowCount()
            self.insertRow(row)
            kind = detect_entry_kind_from_view(entry)
            title = QTableWidgetItem(entry.title)
            title.setData(int(Qt.ItemDataRole.UserRole), entry.uuid)
            icon = entry_kind_icon(kind)
            fav = cached_favicon(entry.url)
            if fav is not None:
                icon = QIcon(str(fav))
            title.setIcon(icon)
            tip = f"{entry.title} ({kind.value})"
            if entry.tags:
                tip += f" [{', '.join(entry.tags)}]"
            title.setToolTip(tip)
            self.setItem(row, 0, title)
            self.setItem(row, 1, QTableWidgetItem(entry.username))
            self.setItem(row, 2, QTableWidgetItem(entry.url))
        self.setSortingEnabled(True)

    def selected_entry_uuid(self) -> str | None:
        items = self.selectedItems()
        if not items:
            return None
        row = items[0].row()
        title_item = self.item(row, 0)
        if title_item is None:
            return None
        uuid = title_item.data(int(Qt.ItemDataRole.UserRole))
        return str(uuid) if uuid else None

    def _on_selection(self) -> None:
        uuid = self.selected_entry_uuid()
        if uuid:
            self.entry_selected.emit(uuid)

    def _on_sort(self, logical_index: int) -> None:
        pass
