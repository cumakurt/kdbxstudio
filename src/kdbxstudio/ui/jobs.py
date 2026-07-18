"""Background job helpers for PySide6 (QThreadPool)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

T = TypeVar("T")


class JobSignals(QObject):
    """Signals emitted from a worker runnable onto the main thread."""

    succeeded = Signal(object)
    failed = Signal(str)


class _FnRunnable(QRunnable):
    def __init__(self, fn: Callable[[], T], signals: JobSignals) -> None:
        super().__init__()
        self._fn = fn
        self._signals = signals
        self.setAutoDelete(True)

    def run(self) -> None:  # noqa: N802
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001 — surface message to UI
            self._signals.failed.emit(str(exc))
            return
        self._signals.succeeded.emit(result)


def run_in_thread_pool(
    fn: Callable[[], T],
    *,
    on_success: Callable[[T], None],
    on_error: Callable[[str], None],
    parent: QObject | None = None,
    pool: QThreadPool | None = None,
) -> JobSignals:
    """Run ``fn`` off the GUI thread; callbacks execute on the receiver thread."""
    signals = JobSignals(parent)
    signals.succeeded.connect(on_success)
    signals.failed.connect(on_error)
    runnable = _FnRunnable(fn, signals)
    (pool or QThreadPool.globalInstance()).start(runnable)
    return signals
