"""Empty-state dashboard when no database is open."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.i18n import tr


class EmptyWorkspaceWidget(QWidget):
    """First-run / locked overview: open, create, recent databases."""

    open_requested = Signal()
    create_requested = Signal()
    palette_requested = Signal()
    recent_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("emptyWorkspace")

        title = QLabel(tr("KDBXStudio"))
        title.setObjectName("emptyBrand")

        subtitle = QLabel(tr("Secure. Modern. yours."))
        subtitle.setObjectName("emptySubtitle")
        subtitle.setWordWrap(True)

        open_btn = QPushButton(tr("Open Database…"))
        open_btn.setProperty("cssClass", "primary")
        open_btn.setDefault(True)
        open_btn.clicked.connect(self.open_requested.emit)

        create_btn = QPushButton(tr("New Database…"))
        create_btn.clicked.connect(self.create_requested.emit)

        palette_btn = QPushButton(tr("⌘ Command Palette"))
        palette_btn.clicked.connect(self.palette_requested.emit)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(open_btn)
        actions.addWidget(create_btn)
        actions.addWidget(palette_btn)
        actions.addStretch()

        recent_label = QLabel(tr("Recent"))
        recent_label.setObjectName("emptyTitle")
        self._recent = QListWidget()
        self._recent.setAccessibleName(tr("Recent databases"))
        self._recent.setMaximumHeight(160)
        self._recent.itemActivated.connect(self._on_recent)

        card = QWidget()
        card.setObjectName("emptyCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(12)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(8)
        card_layout.addLayout(actions)
        card_layout.addSpacing(16)
        card_layout.addWidget(recent_label)
        card_layout.addWidget(self._recent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.addStretch()
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch()

        self._paths: list[Path] = []

    def set_recent(self, paths: list[Path]) -> None:
        self._paths = list(paths)
        self._recent.clear()
        if not paths:
            item = QListWidgetItem(tr("No recent databases"))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._recent.addItem(item)
            return
        for path in paths:
            self._recent.addItem(QListWidgetItem(str(path)))

    def _on_recent(self, item: QListWidgetItem) -> None:
        row = self._recent.row(item)
        if 0 <= row < len(self._paths):
            self.recent_requested.emit(self._paths[row])
