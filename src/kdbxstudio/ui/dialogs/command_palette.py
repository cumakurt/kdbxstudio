"""Command Palette — keyboard-first action launcher."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.ui.theme import current_ui_scale


@dataclass(frozen=True)
class PaletteAction:
    id: str
    title: str
    keywords: tuple[str, ...]
    callback: Callable[[], None]
    section: str = "Actions"


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
        self.resize(scale.px(480), scale.px(360))
        self.setMinimumWidth(scale.px(360))
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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        header = QHBoxLayout()
        header.addWidget(QLabel("Command Palette"))
        header.addStretch()
        header.addWidget(self._hint)
        layout.addLayout(header)
        layout.addWidget(self._input)
        layout.addWidget(self._list)

        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self.reject)
        self._rebuild_list()
        self._input.setFocus()
        self._fade_in()

    def _fade_in(self) -> None:
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(140)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._fade_anim = anim

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
            item = QListWidgetItem(f"{action.section}  ·  {action.title}")
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
