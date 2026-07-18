"""Subtle motion helpers for premium desktop polish (120–180ms)."""

from __future__ import annotations

from enum import IntEnum

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


class MotionDuration(IntEnum):
    INSTANT = 0
    FAST = 120
    NORMAL = 160
    SLOW = 180


def _out_cubic() -> QEasingCurve:
    return QEasingCurve(QEasingCurve.Type.OutCubic)


def fade_in(
    widget: QWidget,
    *,
    duration: int = MotionDuration.NORMAL,
    start: float = 0.0,
    end: float = 1.0,
) -> QPropertyAnimation:
    """Fade a widget in; returns the running animation (keep a reference)."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(start)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(max(0, int(duration)))
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(_out_cubic())
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def slide_in(
    widget: QWidget,
    *,
    axis: str = "y",
    offset: int = 12,
    duration: int = MotionDuration.NORMAL,
) -> QPropertyAnimation:
    """Slide widget from a small offset into its current position."""
    end = widget.pos()
    if axis.lower() == "x":
        start = QPoint(end.x() - offset, end.y())
    else:
        start = QPoint(end.x(), end.y() - offset)
    widget.move(start)
    anim = QPropertyAnimation(widget, b"pos", widget)
    anim.setDuration(max(0, int(duration)))
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(_out_cubic())
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def fade_and_slide_in(
    widget: QWidget,
    *,
    duration: int = MotionDuration.NORMAL,
    offset: int = 10,
) -> tuple[QPropertyAnimation, QPropertyAnimation]:
    """Combined fade + slight vertical slide (e.g. command palette)."""
    fade = fade_in(widget, duration=duration)
    slide = slide_in(widget, axis="y", offset=offset, duration=duration)
    return fade, slide
