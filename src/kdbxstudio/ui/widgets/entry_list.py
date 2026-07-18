"""Entry list as QTableView + model for cheaper large-vault updates."""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractTableModel,
    QMimeData,
    QModelIndex,
    QPoint,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QMenu,
    QTableView,
    QWidget,
)

from kdbxstudio.application.favicon import cached_favicon
from kdbxstudio.core.database import EntryView
from kdbxstudio.i18n import tr
from kdbxstudio.ui.icons.entry_type import detect_entry_kind_from_view, entry_kind_icon
from kdbxstudio.ui.theme.geometry import density_metrics

ENTRY_MIME = "application/x-kdbxstudio-entry"


def _row_height() -> int:
    try:
        from kdbxstudio.ui.theme.manager import current_density

        return density_metrics(current_density()).row_height
    except Exception:
        return 32


class EntryTableModel(QAbstractTableModel):
    """Lazy icon decoration; secrets are not shown in the table."""

    COLUMNS = ("Title", "Username", "URL")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entries: list[EntryView] = []
        self._sort_column = 0
        self._sort_order = Qt.SortOrder.AscendingOrder

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent is not None and parent.isValid():
            return 0
        return len(self._entries)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent is not None and parent.isValid():
            return 0
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and 0 <= section < len(self.COLUMNS)
        ):
            return tr(self.COLUMNS[section])
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if not index.isValid():
            return None
        entry = self._entries[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return entry.title
            if col == 1:
                return entry.username
            if col == 2:
                return entry.url
        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            kind = detect_entry_kind_from_view(entry)
            fav = cached_favicon(entry.url)
            if fav is not None:
                return QIcon(str(fav))
            return entry_kind_icon(kind)
        if role == Qt.ItemDataRole.ToolTipRole and col == 0:
            kind = detect_entry_kind_from_view(entry)
            tip = f"{entry.title} ({kind.value})"
            if entry.tags:
                tip += f" [{', '.join(entry.tags)}]"
            return tip
        if role == Qt.ItemDataRole.UserRole and col == 0:
            return entry.uuid
        return None

    def flags(self, index: QModelIndex):  # noqa: N802
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDragEnabled
        )

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:  # noqa: N802
        if column < 0 or column >= len(self.COLUMNS):
            return
        self._sort_column = column
        self._sort_order = order
        reverse = order == Qt.SortOrder.DescendingOrder

        def key(entry: EntryView) -> str:
            if column == 0:
                return (entry.title or "").lower()
            if column == 1:
                return (entry.username or "").lower()
            return (entry.url or "").lower()

        self.layoutAboutToBeChanged.emit()
        self._entries.sort(key=key, reverse=reverse)
        self.layoutChanged.emit()

    def set_entries(self, entries: list[EntryView]) -> None:
        self.beginResetModel()
        self._entries = list(entries)
        self.endResetModel()
        if self._entries:
            self.sort(self._sort_column, self._sort_order)

    def entry_at(self, row: int) -> EntryView | None:
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

    def mimeTypes(self) -> list[str]:  # noqa: N802
        return [ENTRY_MIME]

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:  # noqa: N802
        data = QMimeData()
        for index in indexes:
            if index.column() != 0:
                continue
            uuid = index.data(Qt.ItemDataRole.UserRole)
            if uuid:
                data.setData(ENTRY_MIME, str(uuid).encode("utf-8"))
                break
        return data


class EntryListWidget(QTableView):
    """Shows entries for the selected group."""

    COLUMNS = EntryTableModel.COLUMNS
    entry_selected = Signal(str)
    delete_requested = Signal()
    permanent_delete_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = EntryTableModel(self)
        self.setModel(self._model)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionsClickable(True)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._header_context_menu)
        self.setIconSize(QSize(16, 16))
        self.setSortingEnabled(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        row_h = _row_height()
        self.verticalHeader().setDefaultSectionSize(row_h)
        self.setIconSize(QSize(max(16, row_h - 12), max(16, row_h - 12)))
        self.selectionModel().selectionChanged.connect(self._on_selection)
        QShortcut(QKeySequence.StandardKey.SelectAll, self, self.selectAll)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self.delete_requested.emit)
        QShortcut(
            QKeySequence("Shift+Delete"),
            self,
            self.permanent_delete_requested.emit,
        )

    def apply_density(self) -> None:
        """Refresh row height from the current UI density."""
        row_h = _row_height()
        self.verticalHeader().setDefaultSectionSize(row_h)
        self.setIconSize(QSize(max(16, row_h - 12), max(16, row_h - 12)))

    def select_row_at(self, pos: QPoint) -> bool:
        index = self.indexAt(pos)
        if not index.isValid():
            return False
        row = index.row()
        selected = {i.row() for i in self.selectionModel().selectedRows()}
        if row not in selected:
            self.selectRow(row)
        return True

    def set_entries(self, entries: list[EntryView]) -> None:
        self._model.set_entries(entries)

    def selected_entry_uuid(self) -> str | None:
        uuids = self.selected_entry_uuids()
        return uuids[0] if uuids else None

    def selected_entry_uuids(self) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for index in self.selectionModel().selectedRows(0):
            uuid = index.data(Qt.ItemDataRole.UserRole)
            if not uuid:
                continue
            text = str(uuid)
            if text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result

    def _header_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        header = self.horizontalHeader()
        for col, name in enumerate(self.COLUMNS):
            action = QAction(tr(name), menu)
            action.setCheckable(True)
            action.setChecked(not header.isSectionHidden(col))
            # Keep at least one column visible.
            visible_count = sum(
                1 for c in range(len(self.COLUMNS)) if not header.isSectionHidden(c)
            )
            if action.isChecked() and visible_count <= 1:
                action.setEnabled(False)

            def _toggle(checked: bool, column: int = col) -> None:
                header.setSectionHidden(column, not checked)

            action.toggled.connect(_toggle)
            menu.addAction(action)
        menu.exec(header.mapToGlobal(pos))

    def _on_selection(self, *_args) -> None:
        uuid = self.selected_entry_uuid()
        if uuid:
            self.entry_selected.emit(uuid)
