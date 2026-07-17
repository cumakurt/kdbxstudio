"""Application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from kdbxstudio.security.store import load_settings
from kdbxstudio.ui.main_window import MainWindow
from kdbxstudio.ui.theme import ThemeMode, apply_theme
from kdbxstudio.ui.theme.scale import configure_high_dpi


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv
    configure_high_dpi()
    app = QApplication(args)
    app.setApplicationName("KDBXStudio")
    app.setOrganizationName("KDBXStudio")
    settings = load_settings()
    try:
        mode = ThemeMode(settings.theme)
    except ValueError:
        mode = ThemeMode.DARK
    apply_theme(app, mode)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
