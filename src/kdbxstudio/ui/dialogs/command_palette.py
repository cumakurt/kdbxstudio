"""Command Palette — keyboard-first action launcher."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.ui.icons import menu_icon
from kdbxstudio.ui.theme import MotionDuration, current_ui_scale, fade_in


@dataclass(frozen=True)
class PaletteAction:
    id: str
    title: str
    keywords: tuple[str, ...]
    callback: Callable[[], None]
    section: str = "Actions"
    icon: str = "terminal"
    shortcut: str = ""


def score_action(action: PaletteAction, query: str) -> int:
    q = query.lower().strip()
    if not q:
        return 1
    hay = " ".join([action.title, action.section, *action.keywords]).lower()
    if hay.startswith(q):
        return 100
    if q in hay:
        return 50
    tokens = q.split()
    if tokens and all(tok in hay for tok in tokens):
        return 40
    return 0


class CommandPalette(QDialog):
    """Fuzzy-filtered command launcher (Ctrl+K)."""

    def __init__(
        self,
        actions: list[PaletteAction],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        scale = current_ui_scale()
        self.resize(scale.px(520), scale.px(380))
        self.setMinimumWidth(scale.px(380))
        self._actions = actions
        self._filtered: list[PaletteAction] = list(actions)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a command…")
        self._input.textChanged.connect(self._filter)
        self._input.returnPressed.connect(self._activate)

        self._list = QListWidget()
        self._list.itemActivated.connect(lambda _i: self._activate())
        self._hint = QLabel("↑↓ navigate · Enter run · Esc close")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(16, 12, 16, 8)
        header.addWidget(QLabel("Command Palette"))
        header.addStretch()
        header.addWidget(self._hint)
        layout.addLayout(header)

        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 0, 12, 8)
        input_layout.addWidget(self._input)
        layout.addWidget(input_container)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(4, 0, 4, 4)
        list_layout.addWidget(self._list)
        layout.addWidget(list_container, 1)

        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self.reject)
        self._rebuild_list()
        self._input.setFocus()
        self._fade_anim = fade_in(self, duration=MotionDuration.NORMAL)

    def _filter(self, text: str) -> None:
        scored: list[tuple[int, PaletteAction]] = []
        for action in self._actions:
            score = score_action(action, text)
            if score > 0:
                scored.append((score, action))
        scored.sort(key=lambda pair: (-pair[0], pair[1].title.lower()))
        self._filtered = [a for _, a in scored]
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        self._list.clear()
        for action in self._filtered:
            label = action.title
            if action.shortcut:
                label = f"{action.title}    {action.shortcut}"
            item = QListWidgetItem(menu_icon(action.icon or "terminal"), label)
            item.setData(Qt.ItemDataRole.UserRole, action.id)
            self._list.addItem(item)
        if self._filtered:
            self._list.setCurrentRow(0)

    def _activate(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._filtered):
            return
        action = self._filtered[row]
        self.accept()
        action.callback()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self._list.setFocus()
            self._list.keyPressEvent(event)
            self._input.setFocus()
            return
        super().keyPressEvent(event)
