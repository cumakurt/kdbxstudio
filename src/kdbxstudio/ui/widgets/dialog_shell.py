"""Shared premium dialog chrome: icon title, subtitle, primary/secondary footer."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.ui.icons import icon


class DialogShell(QDialog):
    """Base dialog with consistent header and button styling."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str = "",
        subtitle: str = "",
        icon_name: str = "info",
        width: int = 480,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(width, 200)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(12)
        self._icon_label = QLabel()
        self._icon_label.setPixmap(icon(icon_name, size=28, brand=True).pixmap(28, 28))
        self._icon_label.setFixedSize(32, 32)
        header.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignTop)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        self._title_label = QLabel(title)
        self._title_label.setObjectName("dialogTitle")
        titles.addWidget(self._title_label)
        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setObjectName("dialogSubtitle")
        self._subtitle_label.setWordWrap(True)
        self._subtitle_label.setVisible(bool(subtitle))
        titles.addWidget(self._subtitle_label)
        header.addLayout(titles, 1)
        root.addLayout(header)

        self.body = QVBoxLayout()
        self.body.setSpacing(12)
        root.addLayout(self.body, 1)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        ok = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if ok is not None:
            ok.setProperty("cssClass", "primary")
            ok.setDefault(True)
            style = ok.style()
            if style is not None:
                style.unpolish(ok)
                style.polish(ok)
        if cancel is not None:
            cancel.setProperty("cssClass", "secondary")
            style = cancel.style()
            if style is not None:
                style.unpolish(cancel)
                style.polish(cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        root.addWidget(self.button_box)

    def set_primary_text(self, text: str) -> None:
        ok = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok is not None:
            ok.setText(text)

    def set_subtitle(self, text: str) -> None:
        self._subtitle_label.setText(text)
        self._subtitle_label.setVisible(bool(text))

    def add_primary_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("cssClass", "primary")
        self.button_box.addButton(btn, QDialogButtonBox.ButtonRole.AcceptRole)
        return btn
