"""pytest-qt smoke tests for MainWindow shell."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from kdbxstudio.ui.dialogs.command_palette import CommandPalette, PaletteAction
from kdbxstudio.ui.main_window import MainWindow


def test_main_window_constructs(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.windowTitle().startswith("KDBXStudio")
    assert window._stack.currentWidget() is window._empty


def test_command_palette_opens_with_fade(qtbot) -> None:
    called = {"ok": False}

    def run() -> None:
        called["ok"] = True

    palette = CommandPalette(
        [PaletteAction("t", "Test Action", ("test",), run)],
    )
    qtbot.addWidget(palette)
    palette.show()
    assert palette.graphicsEffect() is not None
    qtbot.keyClicks(palette._input, "test")
    qtbot.keyClick(palette._input, Qt.Key.Key_Return)
    assert called["ok"] is True
    assert palette.result() == QDialog.DialogCode.Accepted
