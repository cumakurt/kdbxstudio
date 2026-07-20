"""Entry history browser widget with field diff."""

from __future__ import annotations

from html import escape

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.application.history_diff import diff_history
from kdbxstudio.core.database import HistoryView
from kdbxstudio.i18n import tr, trf
from kdbxstudio.ui.theme.manager import current_tokens


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
        self._empty = QLabel(tr("No history for this entry."))
        self._restore = QPushButton(tr("Restore selected revision"))
        self._restore.setEnabled(False)
        self._restore.clicked.connect(self._emit_restore)
        self._reveal = QPushButton(tr("Reveal secrets"))
        self._reveal.setCheckable(True)
        self._reveal.toggled.connect(self._refresh_detail)

        self._list.currentRowChanged.connect(self._on_row)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_list_menu)

        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        left.addWidget(QLabel(tr("Revisions")))
        left.addWidget(self._list)
        left.addWidget(self._restore)
        left.addWidget(self._reveal)
        left.addWidget(self._empty)
        right = QVBoxLayout()
        right.addWidget(QLabel(tr("Snapshot / diff vs newer")))
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
            label = item.modified or trf("Revision {index}", index=item.index)
            title = item.title or tr("(untitled)")
            row = QListWidgetItem(f"{label} — {title}")
            self._list.addItem(row)
        if items:
            self._list.setCurrentRow(0)

    def _emit_restore(self) -> None:
        row = self._list.currentRow()
        if 0 <= row < len(self._items):
            self.restore_requested.emit(self._items[row].index)

    def _show_list_menu(self, pos: QPoint) -> None:
        item = self._list.itemAt(pos)
        if item is not None:
            self._list.setCurrentItem(item)
        row = self._list.currentRow()
        has_item = 0 <= row < len(self._items)
        menu = QMenu(self)
        restore = menu.addAction(tr("Restore selected revision"), self._emit_restore)
        restore.setEnabled(has_item)
        reveal = menu.addAction(
            tr("Reveal secrets")
            if not self._reveal.isChecked()
            else tr("Hide secrets"),
            lambda: self._reveal.toggle(),
        )
        reveal.setEnabled(has_item)
        menu.exec(self._list.mapToGlobal(pos))

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
            f"{tr('Title')}: {item.title}",
            f"{tr('Username')}: {item.username}",
            f"{tr('Password')}: {password}",
            f"{tr('URL')}: {item.url}",
            f"{tr('OTP:')} {otp}",
            f"{tr('Modified:')} {item.modified}",
            "",
            tr("Notes:"),
            item.notes,
        ]
        html_parts = [f"<pre>{escape(chr(10).join(lines))}</pre>"]
        if row > 0:
            newer = self._items[row - 1]
            diffs = diff_history(item, newer, mask_secrets=not reveal)
            tokens = current_tokens()
            html_parts.append(f"<h3>{escape(tr('Diff vs newer revision:'))}</h3>")
            if not diffs:
                html_parts.append(f"<p>{escape(tr('(no field changes)'))}</p>")
            else:
                html_parts.append("<table cellspacing='4'>")
                for diff in diffs:
                    if not diff.before and diff.after:
                        color = tokens.text_success
                        kind = tr("added")
                    elif diff.before and not diff.after:
                        color = tokens.text_danger
                        kind = tr("removed")
                    else:
                        color = tokens.text_warning
                        kind = tr("changed")
                    html_parts.append(
                        "<tr>"
                        f"<td><b>{escape(diff.field)}</b></td>"
                        f"<td style='color:{color}'>{escape(kind)}</td>"
                        f"<td><code>{escape(diff.before)}</code></td>"
                        f"<td>→</td>"
                        f"<td><code>{escape(diff.after)}</code></td>"
                        "</tr>"
                    )
                html_parts.append("</table>")
        self._detail.setHtml("".join(html_parts))
