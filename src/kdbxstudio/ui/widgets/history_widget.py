"""Entry history browser widget with field diff."""

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

from kdbxstudio.application.history_diff import diff_history
from kdbxstudio.core.database import HistoryView


def _mask_secret(value: str) -> str:
    return "••••••••" if value else ""


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
        self._reveal = QPushButton("Reveal secrets")
        self._reveal.setCheckable(True)
        self._reveal.toggled.connect(self._refresh_detail)

        self._list.currentRowChanged.connect(self._on_row)

        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        left.addWidget(QLabel("Revisions"))
        left.addWidget(self._list)
        left.addWidget(self._restore)
        left.addWidget(self._reveal)
        left.addWidget(self._empty)
        right = QVBoxLayout()
        right.addWidget(QLabel("Snapshot / diff vs newer"))
        right.addWidget(self._detail)
        layout.addLayout(left, 1)
        layout.addLayout(right, 2)

    def clear(self) -> None:
        self._items = []
        self._list.clear()
        self._detail.clear()
        self._empty.show()
        self._restore.setEnabled(False)
        self._reveal.setChecked(False)

    def set_history(self, items: list[HistoryView]) -> None:
        self._items = items
        self._list.clear()
        self._detail.clear()
        self._empty.setVisible(not items)
        self._restore.setEnabled(False)
        self._reveal.setChecked(False)
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
        self._restore.setEnabled(True)
        self._refresh_detail()
        self.revision_selected.emit(self._items[row].index)

    def _refresh_detail(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._items):
            self._detail.clear()
            return
        item = self._items[row]
        reveal = self._reveal.isChecked()
        password = item.password if reveal else _mask_secret(item.password)
        otp = item.otp if reveal else _mask_secret(item.otp)
        lines = [
            f"Title: {item.title}",
            f"Username: {item.username}",
            f"Password: {password}",
            f"URL: {item.url}",
            f"OTP: {otp}",
            f"Modified: {item.modified}",
            "",
            "Notes:",
            item.notes,
        ]
        if row > 0:
            newer = self._items[row - 1]
            diffs = diff_history(item, newer, mask_secrets=not reveal)
            lines.append("")
            lines.append("Diff vs newer revision:")
            if not diffs:
                lines.append("(no field changes)")
            for diff in diffs:
                lines.append(f"- {diff.field}: {diff.before!r} → {diff.after!r}")
        self._detail.setPlainText("\n".join(lines))
