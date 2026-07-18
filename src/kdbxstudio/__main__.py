"""Application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from kdbxstudio.i18n import set_language
from kdbxstudio.security.store import load_settings
from kdbxstudio.ui.main_window import MainWindow
from kdbxstudio.ui.theme import apply_theme
from kdbxstudio.ui.theme.scale import configure_high_dpi
from kdbxstudio.ui.theme.tokens import parse_theme


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv
    configure_high_dpi()
    app = QApplication(args)
    app.setApplicationName("KDBXStudio")
    app.setOrganizationName("KDBXStudio")
    settings = load_settings()
    set_language(settings.language)
    apply_theme(
        app,
        parse_theme(settings.theme),
        accent=settings.accent,
        ui_density=settings.ui_density,
        ui_scale_percent=settings.ui_scale_percent,
        font_size=settings.font_size,
        menu_size=settings.menu_size,
    )
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
