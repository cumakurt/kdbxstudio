"""Group tree widget."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QAbstractItemView, QFrame, QTreeWidget, QTreeWidgetItem

from kdbxstudio.core.database import GroupView
from kdbxstudio.i18n import tr
from kdbxstudio.ui.icons.group_icons import group_icon_for_name
from kdbxstudio.ui.widgets.entry_list import ENTRY_MIME


class GroupTreeWidget(QTreeWidget):
    """Hierarchical group browser with colorful auto-assigned category icons."""

    group_selected = Signal(str)
    entry_drop_requested = Signal(str, str)  # entry_uuid, group_uuid

    def __init__(self, parent: QTreeWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderLabel(tr("Groups"))
        self.setUniformRowHeights(True)
        self.setIconSize(QSize(20, 20))
        self.setIndentation(18)
        self.setRootIsDecorated(True)
        self.setItemsExpandable(True)
        self.setAnimated(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAlternatingRowColors(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.itemSelectionChanged.connect(self._on_selection)

    def select_at(self, pos: QPoint) -> bool:
        item = self.itemAt(pos)
        if item is None:
            return False
        self.setCurrentItem(item)
        return True

    def set_groups(
        self,
        groups: list[GroupView],
        root_uuid: str,
        *,
        select_uuid: str | None = None,
    ) -> None:
        self.blockSignals(True)
        try:
            self.clear()
            by_uuid: dict[str, GroupView] = {g.uuid: g for g in groups}
            items: dict[str, QTreeWidgetItem] = {}

            for group in groups:
                label = group.name or tr("(unnamed)")
                if group.is_recycle_bin:
                    label = f"[Bin] {label}"
                item = QTreeWidgetItem([label])
                item.setData(0, Qt.ItemDataRole.UserRole, group.uuid)
                item.setIcon(
                    0,
                    group_icon_for_name(
                        group.name,
                        is_recycle_bin=group.is_recycle_bin,
                        size=20,
                    ),
                )
                items[group.uuid] = item

            roots: list[QTreeWidgetItem] = []
            for group in groups:
                item = items[group.uuid]
                parent_uuid = group.parent_uuid
                if parent_uuid and parent_uuid in items and parent_uuid in by_uuid:
                    items[parent_uuid].addChild(item)
                else:
                    roots.append(item)

            if root_uuid in items:
                self.addTopLevelItem(items[root_uuid])
            else:
                for item in roots:
                    self.addTopLevelItem(item)

            self.expandAll()
            target = select_uuid if select_uuid and select_uuid in items else root_uuid
            if target in items:
                self.setCurrentItem(items[target])
        finally:
            self.blockSignals(False)

    def selected_group_uuid(self) -> str | None:
        items = self.selectedItems()
        if not items:
            return None
        value = items[0].data(0, Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def select_uuid(self, group_uuid: str) -> bool:
        def walk(item: QTreeWidgetItem) -> bool:
            value = item.data(0, Qt.ItemDataRole.UserRole)
            if str(value) == group_uuid:
                self.setCurrentItem(item)
                return True
            for index in range(item.childCount()):
                if walk(item.child(index)):
                    return True
            return False

        for index in range(self.topLevelItemCount()):
            top = self.topLevelItem(index)
            if top is not None and walk(top):
                return True
        return False

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(ENTRY_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(ENTRY_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        if not event.mimeData().hasFormat(ENTRY_MIME):
            event.ignore()
            return
        raw = bytes(event.mimeData().data(ENTRY_MIME).data()).decode("utf-8")
        entry_uuid = raw.strip()
        if not entry_uuid:
            event.ignore()
            return
        item = self.itemAt(event.position().toPoint())
        if item is None:
            event.ignore()
            return
        group_uuid = item.data(0, Qt.ItemDataRole.UserRole)
        if not group_uuid:
            event.ignore()
            return
        self.entry_drop_requested.emit(entry_uuid, str(group_uuid))
        event.acceptProposedAction()

    def _on_selection(self) -> None:
        uuid = self.selected_group_uuid()
        if uuid:
            self.group_selected.emit(uuid)
