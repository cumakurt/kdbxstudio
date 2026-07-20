"""Floating toast notifications."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from kdbxstudio.ui.theme.manager import set_widget_tone
from kdbxstudio.ui.theme.motion import fade_in


class ToastHost(QWidget):
    """Bottom-center toast overlay parented to a host widget."""

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self._host = host
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._label = QLabel()
        self._label.setObjectName("toastBanner")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self._anim: QPropertyAnimation | None = None
        host.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if watched is self._host and event.type() == QEvent.Type.Resize:
            self._reposition()
        return super().eventFilter(watched, event)

    def show_message(self, text: str, timeout_ms: int = 3000, tone: str = "") -> None:
        if not text:
            return
        self._label.setText(text)
        set_widget_tone(self._label, tone or "")
        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()
        self._anim = fade_in(self)
        self._timer.start(max(500, int(timeout_ms)))

    def _reposition(self) -> None:
        host = self._host
        self.adjustSize()
        w = min(self.sizeHint().width() + 32, max(160, host.width() - 64))
        self.setFixedWidth(w)
        self.adjustSize()
        x = (host.width() - self.width()) // 2
        y = host.height() - self.height() - 56
        self.move(max(12, x), max(12, y))
