#!/usr/bin/env python3
"""Create a sample KDBX, exercise MainWindow, and capture screenshots."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "visual"
SAMPLE = OUT / "sample.kdbx"
PASSWORD = "demo-pass-123"


def build_sample_db(path: Path) -> None:
    from kdbxstudio.application.database_manager import DatabaseManager

    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    mgr = DatabaseManager()
    mgr.create(path, password=PASSWORD)
    root = mgr.root_group_uuid()
    work = mgr.add_group(root, "Work")
    personal = mgr.add_group(root, "Personal")
    mgr.add_entry(
        work.uuid,
        title="GitHub",
        username="dev@example.com",
        password="StrongPass!2024",
        url="https://github.com",
        notes="Work account",
    )
    mgr.add_entry(
        work.uuid,
        title="Weak VPN",
        username="vpn",
        password="1234",
        url="https://vpn.example",
    )
    mgr.add_entry(
        work.uuid,
        title="API Shared A",
        username="api",
        password="same-secret-xyz",
    )
    mgr.add_entry(
        work.uuid,
        title="API Shared B",
        username="api",
        password="same-secret-xyz",
    )
    mgr.add_entry(
        work.uuid,
        title="Deploy SSH",
        username="deploy",
        password="",
        notes=(
            "-----BEGIN OPENSSH PRIVATE KEY-----\n"
            "demo\n"
            "-----END OPENSSH PRIVATE KEY-----\n"
        ),
    )
    mgr.add_entry(
        personal.uuid,
        title="Email",
        username="me@example.com",
        password="Mailbox#Safe99",
        url="https://mail.example.com",
        notes="Personal inbox",
    )
    mgr.add_entry(
        personal.uuid,
        title="Empty Secret",
        username="",
        password="",
    )
    mgr.save()
    mgr.close_all()


def grab(window, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    pix = window.grab()
    assert not pix.isNull(), f"Failed to grab {name}"
    ok = pix.save(str(path), "PNG")
    assert ok, f"Failed to save {path}"
    print(f"saved {path} ({pix.width()}x{pix.height()})")
    return path


def main() -> int:
    build_sample_db(SAMPLE)

    from kdbxstudio.ui.dialogs.command_palette import CommandPalette, PaletteAction
    from kdbxstudio.ui.main_window import MainWindow
    from kdbxstudio.ui.theme import ThemeMode, apply_theme
    from kdbxstudio.ui.theme.scale import configure_high_dpi

    configure_high_dpi()
    app = QApplication(sys.argv)
    app.setApplicationName("KDBXStudio")
    apply_theme(app, ThemeMode.DARK)

    window = MainWindow()
    window.resize(1100, 700)
    window.show()
    app.processEvents()
    grab(window, "01_empty_dashboard")

    window._dbm.open(SAMPLE, password=PASSWORD)
    app.processEvents()
    assert window._dbm.active is not None
    assert window._stack.currentIndex() == 1

    entries = window._dbm.all_entries()
    assert len(entries) >= 6, f"expected sample entries, got {len(entries)}"
    github = next(e for e in entries if e.title == "GitHub")
    window._show_entry(github.uuid)
    window._entry_list.set_entries(entries)
    window._refresh_audit()
    app.processEvents()
    report = window._audit.run()
    assert report.total_entries >= 6
    assert report.findings, "audit should report sample issues"
    grab(window, "02_workspace_open")

    # Show SSH-detected entry icons
    ssh = next(e for e in entries if e.title == "Deploy SSH")
    window._show_entry(ssh.uuid)
    app.processEvents()
    grab(window, "02b_ssh_entry_icons")

    window._search_box.setText("GitHub")
    window._run_search()
    app.processEvents()
    assert window._entry_list.rowCount() >= 1
    grab(window, "03_search_github")

    palette = CommandPalette(
        [
            PaletteAction("save", "Save", ("save",), window.save_database),
            PaletteAction("audit", "Refresh Audit", ("audit",), window._refresh_audit),
        ],
        window,
    )
    palette.show()
    app.processEvents()
    grab(palette, "04_command_palette")
    palette.close()

    window._entry_tabs.setCurrentIndex(4)
    app.processEvents()
    grab(window, "05_certs_tab")

    # Generator dialog
    from kdbxstudio.ui.dialogs.password_generator_dialog import PasswordGeneratorDialog

    gen = PasswordGeneratorDialog(window)
    gen.show()
    app.processEvents()
    grab(gen, "06_password_generator")
    gen.close()

    print(
        f"OK sample={SAMPLE} entries={len(entries)} "
        f"findings={len(report.findings)} "
        f"weak={report.weak_passwords} empty={report.empty_passwords}"
    )
    QTimer.singleShot(50, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
