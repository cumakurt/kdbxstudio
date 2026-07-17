"""Live TOTP display widget."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.core.totp import current_totp


class TotpWidget(QWidget):
    """Shows a refreshing TOTP code for the selected entry."""

    copy_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._otp_value = ""
        self._last_code = ""
        self._code = QLabel("------")
        self._code.setStyleSheet(
            "font-size: 18px; font-weight: 600; letter-spacing: 1px;"
        )
        self._label = QLabel("No TOTP configured")
        self._remaining = QProgressBar()
        self._remaining.setTextVisible(True)
        self._otp_edit = QLineEdit()
        self._otp_edit.setPlaceholderText("otpauth://… or base32 secret")

        copy_btn = QPushButton("Copy code")
        copy_btn.clicked.connect(self._copy)

        top = QHBoxLayout()
        top.addWidget(self._code)
        top.addStretch()
        top.addWidget(copy_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        layout.addLayout(top)
        layout.addWidget(self._remaining)
        layout.addWidget(QLabel("OTP URI / secret"))
        layout.addWidget(self._otp_edit)

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def clear(self) -> None:
        self._otp_value = ""
        self._last_code = ""
        self._otp_edit.clear()
        self._label.setText("No TOTP configured")
        self._code.setText("------")
        self._remaining.setValue(0)

    def set_otp(self, otp: str) -> None:
        self._otp_value = otp or ""
        self._otp_edit.setText(self._otp_value)
        self._tick()

    def otp_value(self) -> str:
        return self._otp_edit.text().strip()

    def _tick(self) -> None:
        value = self._otp_edit.text().strip() or self._otp_value
        status = current_totp(value)
        if not status.valid:
            self._label.setText(status.error or "No TOTP configured")
            self._code.setText("------")
            self._last_code = ""
            self._remaining.setRange(0, 30)
            self._remaining.setValue(0)
            self._remaining.setFormat("")
            return
        self._label.setText(status.label or "TOTP")
        self._last_code = status.code
        code = status.code
        pretty = f"{code[:3]} {code[3:]}" if len(code) == 6 else code
        self._code.setText(pretty)
        self._remaining.setRange(0, status.period)
        self._remaining.setValue(status.remaining_seconds)
        self._remaining.setFormat(f"{status.remaining_seconds}s")

    def _copy(self) -> None:
        if self._last_code:
            self.copy_requested.emit(self._last_code)
