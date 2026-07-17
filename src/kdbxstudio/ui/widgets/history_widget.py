"""Entry history browser widget."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.core.database import HistoryView


class HistoryWidget(QWidget):
    """Lists historical revisions for the selected entry."""

    revision_selected = Signal(int)
    restore_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[HistoryView] = []
        self._list = QListWidget()
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._empty = QLabel("No history for this entry.")
        self._restore = QPushButton("Restore selected revision")
        self._restore.setEnabled(False)
        self._restore.clicked.connect(self._emit_restore)

        self._list.currentRowChanged.connect(self._on_row)

        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        left.addWidget(QLabel("Revisions"))
        left.addWidget(self._list)
        left.addWidget(self._restore)
        left.addWidget(self._empty)
        right = QVBoxLayout()
        right.addWidget(QLabel("Snapshot"))
        right.addWidget(self._detail)
        layout.addLayout(left, 1)
        layout.addLayout(right, 2)

    def clear(self) -> None:
        self._items = []
        self._list.clear()
        self._detail.clear()
        self._empty.show()
        self._restore.setEnabled(False)

    def set_history(self, items: list[HistoryView]) -> None:
        self._items = items
        self._list.clear()
        self._detail.clear()
        self._empty.setVisible(not items)
        self._restore.setEnabled(False)
        for item in items:
            label = item.modified or f"Revision {item.index}"
            title = item.title or "(untitled)"
            row = QListWidgetItem(f"{label} — {title}")
            self._list.addItem(row)
        if items:
            self._list.setCurrentRow(0)

    def _emit_restore(self) -> None:
        row = self._list.currentRow()
        if 0 <= row < len(self._items):
            self.restore_requested.emit(self._items[row].index)

    def _on_row(self, row: int) -> None:
        if row < 0 or row >= len(self._items):
            self._detail.clear()
            self._restore.setEnabled(False)
            return
        item = self._items[row]
        self._restore.setEnabled(True)
        self._detail.setPlainText(
            "\n".join(
                [
                    f"Title: {item.title}",
                    f"Username: {item.username}",
                    f"Password: {item.password}",
                    f"URL: {item.url}",
                    f"OTP: {item.otp}",
                    f"Modified: {item.modified}",
                    "",
                    "Notes:",
                    item.notes,
                ]
            )
        )
        self.revision_selected.emit(item.index)
