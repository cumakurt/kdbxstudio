"""Entry list widget with per-entry type icons and optional favicons."""

from __future__ import annotations

from PySide6.QtCore import QMimeData, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
)

from kdbxstudio.application.favicon import cached_favicon
from kdbxstudio.core.database import EntryView
from kdbxstudio.i18n import tr
from kdbxstudio.ui.icons.entry_type import detect_entry_kind_from_view, entry_kind_icon

ENTRY_MIME = "application/x-kdbxstudio-entry"


class EntryListWidget(QTableWidget):
    """Shows entries for the selected group."""

    entry_selected = Signal(str)
    delete_requested = Signal()
    permanent_delete_requested = Signal()

    COLUMNS = ("Title", "Username", "URL")

    def __init__(self, parent: QTableWidget | None = None) -> None:
        super().__init__(0, len(self.COLUMNS), parent)
        self.setHorizontalHeaderLabels([tr(col) for col in self.COLUMNS])
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setIconSize(QSize(16, 16))
        self.itemSelectionChanged.connect(self._on_selection)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        QShortcut(QKeySequence.StandardKey.SelectAll, self, self.selectAll)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self.delete_requested.emit)
        QShortcut(
            QKeySequence("Shift+Delete"),
            self,
            self.permanent_delete_requested.emit,
        )

    def select_row_at(self, pos: QPoint) -> bool:
        """Select the row under *pos* if it is not already part of the selection."""
        item = self.itemAt(pos)
        if item is None:
            return False
        row = item.row()
        selected_rows = {index.row() for index in self.selectedIndexes()}
        if row not in selected_rows:
            self.selectRow(row)
        return True

    def mimeTypes(self) -> list[str]:
        return [ENTRY_MIME, *super().mimeTypes()]

    def mimeData(self, items: list[QTableWidgetItem]) -> QMimeData:  # type: ignore[override]
        data = super().mimeData(items)
        if data is None:
            data = QMimeData()
        uuid = self.selected_entry_uuid()
        if uuid:
            data.setData(ENTRY_MIME, uuid.encode("utf-8"))
        return data

    def set_entries(self, entries: list[EntryView]) -> None:
        self.setSortingEnabled(False)
        self.clearContents()
        self.setRowCount(len(entries))
        for row, entry in enumerate(entries):
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
        uuids = self.selected_entry_uuids()
        return uuids[0] if uuids else None

    def selected_entry_uuids(self) -> list[str]:
        rows = sorted({index.row() for index in self.selectedIndexes()})
        result: list[str] = []
        seen: set[str] = set()
        for row in rows:
            title_item = self.item(row, 0)
            if title_item is None:
                continue
            uuid = title_item.data(int(Qt.ItemDataRole.UserRole))
            if not uuid:
                continue
            text = str(uuid)
            if text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result

    def _on_selection(self) -> None:
        uuid = self.selected_entry_uuid()
        if uuid:
            self.entry_selected.emit(uuid)
