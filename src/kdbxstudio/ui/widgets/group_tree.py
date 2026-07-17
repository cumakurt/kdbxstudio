"""Group tree widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from kdbxstudio.core.database import GroupView


class GroupTreeWidget(QTreeWidget):
    """Hierarchical group browser."""

    group_selected = Signal(str)

    def __init__(self, parent: QTreeWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderLabel("Groups")
        self.setUniformRowHeights(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.itemSelectionChanged.connect(self._on_selection)

    def set_groups(self, groups: list[GroupView], root_uuid: str) -> None:
        self.clear()
        by_uuid: dict[str, GroupView] = {g.uuid: g for g in groups}
        items: dict[str, QTreeWidgetItem] = {}

        # Build items without parents first
        for group in groups:
            label = group.name or "(unnamed)"
            if group.is_recycle_bin:
                label = f"[Bin] {label}"
            item = QTreeWidgetItem([label])
            item.setData(0, Qt.ItemDataRole.UserRole, group.uuid)
            items[group.uuid] = item

        roots: list[QTreeWidgetItem] = []
        for group in groups:
            item = items[group.uuid]
            parent_uuid = group.parent_uuid
            if parent_uuid and parent_uuid in items and parent_uuid in by_uuid:
                items[parent_uuid].addChild(item)
            else:
                roots.append(item)

        # Prefer attaching under true root when present
        if root_uuid in items:
            self.addTopLevelItem(items[root_uuid])
        else:
            for item in roots:
                self.addTopLevelItem(item)

        self.expandAll()
        if root_uuid in items:
            self.setCurrentItem(items[root_uuid])

    def selected_group_uuid(self) -> str | None:
        items = self.selectedItems()
        if not items:
            return None
        value = items[0].data(0, Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def _on_selection(self) -> None:
        uuid = self.selected_group_uuid()
        if uuid:
            self.group_selected.emit(uuid)
