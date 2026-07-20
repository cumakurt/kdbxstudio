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


def test_main_window_uses_vertical_workspace_on_compact_width(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(640, 700)
    window.show()
    qtbot.wait(10)
    assert window._workspace_splitter.orientation() == Qt.Orientation.Vertical
    assert window._entry_detail._scroll.widgetResizable()


def test_groups_dock_is_freely_resizable(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    dock = window._groups_dock
    assert dock.minimumWidth() <= 160
    assert dock.maximumWidth() >= 720
    # Soft ceiling must not clamp near the old 280px hard limit.
    assert dock.maximumWidth() > 280


def test_main_window_separator_is_grabable() -> None:
    """Dock resize requires a non-zero QMainWindow::separator (was 0px)."""
    from kdbxstudio.ui.theme.styles import build_stylesheet
    from kdbxstudio.ui.theme.tokens import ThemeMode, tokens_for

    css = build_stylesheet(tokens_for(ThemeMode.DARK))
    idx = css.index("QMainWindow::separator")
    block = css[idx : idx + 180]
    assert "width: 0px" not in block
    assert "height: 0px" not in block
    assert "width:" in block
    assert "QMainWindow::separator:hover" in css


def test_groups_dock_ensures_usable_width_after_restore(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1400, 900)
    window.show()
    qtbot.waitExposed(window)
    dock = window._groups_dock
    dock.show()
    qtbot.wait(20)
    # Simulate a collapsed restore by forcing the minimum, then ensure.
    window.resizeDocks([dock], [140], Qt.Orientation.Horizontal)
    qtbot.wait(20)
    assert dock.width() <= 160
    window._ensure_groups_dock_width(preferred=220)
    qtbot.wait(20)
    assert dock.width() >= 200


def test_workspace_splitter_keeps_sizes_across_same_orientation_resize(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1280, 800)
    window.show()
    qtbot.wait(10)
    assert window._workspace_splitter.orientation() == Qt.Orientation.Horizontal
    window._workspace_splitter.setSizes([420, 500])
    before = window._workspace_splitter.sizes()
    window.resize(1400, 800)
    qtbot.wait(10)
    assert window._workspace_splitter.orientation() == Qt.Orientation.Horizontal
    assert window._workspace_splitter.sizes() == before


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
