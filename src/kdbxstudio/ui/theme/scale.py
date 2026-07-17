"""Fixed, compact UI scale — OS HiDPI handles pixel density."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication, QScreen


@dataclass(frozen=True)
class UiScale:
    """Design px multiplier. Kept at 1.0; Qt devicePixelRatio handles HiDPI."""

    factor: float = 1.0

    def px(self, value: int | float) -> int:
        return max(1, int(round(value * self.factor)))

    def font_px(self, value: int | float = 11) -> int:
        return max(10, self.px(value))

    def size(self, width: int, height: int) -> QSize:
        return QSize(self.px(width), self.px(height))


def detect_ui_scale(screen: QScreen | None = None) -> UiScale:
    """Always return baseline scale for a calm, compact desktop UI."""
    _ = screen
    return UiScale(1.0)


def suggested_window_size(
    screen: QScreen | None = None,
    *,
    scale: UiScale | None = None,
) -> QSize:
    """Default main window: ~75% of available screen."""
    _ = scale
    target = screen
    if target is None:
        app = QGuiApplication.instance()
        if isinstance(app, QGuiApplication):
            target = app.primaryScreen()
    if target is None:
        return QSize(1100, 700)

    avail = target.availableGeometry()
    width = min(int(avail.width() * 0.75), 1280)
    height = min(int(avail.height() * 0.75), 780)
    width = max(900, min(width, avail.width() - 32))
    height = max(560, min(height, avail.height() - 32))
    return QSize(width, height)


def configure_high_dpi() -> None:
    """Best-effort HiDPI policy before QApplication is created."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication

    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass
