"""Entry list as QTableView + model for cheaper large-vault updates."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import (
    QAbstractTableModel,
    QMimeData,
    QModelIndex,
    QPersistentModelIndex,
    QPoint,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QAction, QBrush, QColor, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QMenu,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QWidget,
)

from kdbxstudio.application.expiry import entry_list_tone
from kdbxstudio.application.favicon import cached_favicon
from kdbxstudio.core.database import EntryView
from kdbxstudio.i18n import tr
from kdbxstudio.ui.icons.entry_type import detect_entry_kind_from_view, entry_list_icon
from kdbxstudio.ui.theme.geometry import density_metrics
from kdbxstudio.ui.theme.manager import current_tokens

ENTRY_MIME = "application/x-kdbxstudio-entry"

_TONE_ROLE = Qt.ItemDataRole.UserRole + 1
_INVALID_INDEX = QModelIndex()


def _row_height() -> int:
    try:
        from kdbxstudio.ui.theme.manager import current_density

        return density_metrics(current_density()).row_height
    except Exception:
        return 32


def _tone_brush(tone: str | None) -> QBrush | None:
    if not tone:
        return None
    tokens = current_tokens()
    if tone == "danger":
        color = QColor(tokens.text_danger)
    elif tone == "warning":
        color = QColor(tokens.text_warning)
    elif tone == "muted":
        color = QColor(tokens.text_muted)
    elif tone == "success":
        color = QColor(tokens.text_success)
    else:
        return None
    color.setAlpha(36 if tokens.is_dark else 48)
    return QBrush(color)


class _SeverityDelegate(QStyledItemDelegate):
    """Paint a left accent bar for severity-toned rows."""

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:  # noqa: N802
        super().paint(painter, option, index)
        if index.column() != 0:
            return
        tone = index.data(_TONE_ROLE)
        if not tone:
            return
        tokens = current_tokens()
        if tone == "danger":
            color = QColor(tokens.text_danger)
        elif tone == "warning":
            color = QColor(tokens.text_warning)
        elif tone == "muted":
            color = QColor(tokens.border_strong)
        else:
            color = QColor(tokens.brand_primary)
        painter.save()
        painter.fillRect(
            option.rect.x(), option.rect.y(), 3, option.rect.height(), color
        )
        painter.restore()


class EntryTableModel(QAbstractTableModel):
    """Lazy icon decoration; secrets are not shown in the table."""

    COLUMNS = ("Title", "Username", "URL")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entries: list[EntryView] = []
        self._sort_column = 0
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._audit_tones: dict[str, str] = {}

    def set_audit_tones(self, tones: dict[str, str]) -> None:
        self._audit_tones = dict(tones)
        rows = len(self._entries)
        if rows:
            top = self.index(0, 0)
            bottom = self.index(rows - 1, self.columnCount() - 1)
            self.dataChanged.emit(
                top,
                bottom,
                [Qt.ItemDataRole.BackgroundRole, _TONE_ROLE],
            )

    def rowCount(  # noqa: N802
        self, parent: QModelIndex | QPersistentModelIndex = _INVALID_INDEX
    ) -> int:
        if parent.isValid():
            return 0
        return len(self._entries)

    def columnCount(  # noqa: N802
        self, parent: QModelIndex | QPersistentModelIndex = _INVALID_INDEX
    ) -> int:
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object | None:  # noqa: N802
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and 0 <= section < len(self.COLUMNS)
        ):
            return tr(self.COLUMNS[section])
        return None

    def data(  # noqa: N802
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object | None:
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
            size = 16
            parent = self.parent()
            if isinstance(parent, QTableView):
                size = max(16, parent.iconSize().width())
            return entry_list_icon(entry, size=size)
        if role == Qt.ItemDataRole.ToolTipRole and col == 0:
            kind = detect_entry_kind_from_view(entry)
            tip = f"{entry.title} ({kind.value})"
            if entry.tags:
                tip += f" [{', '.join(entry.tags)}]"
            if entry.url and cached_favicon(entry.url) is not None:
                tip += " · favicon"
            tone = entry_list_tone(entry, audit_tone=self._audit_tones.get(entry.uuid))
            if tone:
                tip += f" · {tone}"
            return tip
        if role == Qt.ItemDataRole.UserRole and col == 0:
            return entry.uuid
        if role == _TONE_ROLE:
            return entry_list_tone(entry, audit_tone=self._audit_tones.get(entry.uuid))
        if role == Qt.ItemDataRole.BackgroundRole:
            tone = entry_list_tone(entry, audit_tone=self._audit_tones.get(entry.uuid))
            return _tone_brush(tone)
        return None

    def refresh_icons(self) -> None:
        """Notify views that decoration icons may have changed (e.g. favicon)."""
        rows = len(self._entries)
        if rows == 0:
            return
        top = self.index(0, 0)
        bottom = self.index(rows - 1, 0)
        self.dataChanged.emit(top, bottom, [Qt.ItemDataRole.DecorationRole])

    def flags(  # noqa: N802
        self, index: QModelIndex | QPersistentModelIndex
    ) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDragEnabled
        )

    def sort(
        self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder
    ) -> None:  # noqa: N802
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

    def mimeData(self, indexes: Sequence[QModelIndex]) -> QMimeData:  # noqa: N802
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
    favicon_prefetch_requested = Signal(object)  # list[str] urls

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("entryListPane")
        self._model = EntryTableModel(self)
        self.setModel(self._model)
        self.setItemDelegate(_SeverityDelegate(self))
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.verticalHeader().setVisible(False)
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionsClickable(True)
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        header.setHighlightSections(False)
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
        self.refresh_icons()

    def set_audit_tones(self, tones: dict[str, str]) -> None:
        self._model.set_audit_tones(tones)

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
        urls = [e.url for e in entries if (e.url or "").strip()]
        if urls:
            self.favicon_prefetch_requested.emit(urls)

    def refresh_icons(self) -> None:
        self._model.refresh_icons()

    def retranslate_headers(self) -> None:
        """Notify the view that translated model header labels changed."""
        self._model.headerDataChanged.emit(
            Qt.Orientation.Horizontal,
            0,
            len(self.COLUMNS) - 1,
        )

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

    def _on_selection(self, *_args: object) -> None:
        uuid = self.selected_entry_uuid()
        if uuid:
            self.entry_selected.emit(uuid)
