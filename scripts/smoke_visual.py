#!/usr/bin/env python3
"""Create a sample KDBX, exercise MainWindow, and capture screenshots.

Dev captures go to ``artifacts/visual/`` (gitignored).
README-ready copies go to ``assets/screenshots/`` (committed).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "visual"
README_SHOTS = ROOT / "assets" / "screenshots"
SAMPLE = OUT / "sample.kdbx"
PASSWORD = "demo-pass-123"

# Stable names referenced from README.md
README_EXPORT = {
    "01_empty_dashboard": "01-welcome.png",
    "02_workspace_open": "02-workspace.png",
    "03_search_github": "03-search.png",
    "04_command_palette": "04-command-palette.png",
    "05_security_dashboard": "05-security-dashboard.png",
    "06_password_generator": "06-password-generator.png",
}


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
    github = mgr.add_entry(
        work.uuid,
        title="GitHub",
        username="dev@example.com",
        password="StrongPass!2024-Extra-Long",
        url="https://github.com",
        notes="Work account\n\n- SSH keys in Deploy SSH\n- Rotate quarterly",
        tags=["work", "dev", "favorite"],
    )
    mgr.update_entry(
        github.uuid,
        otp="otpauth://totp/GitHub:dev@example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub",
    )
    mgr.add_entry(
        work.uuid,
        title="Weak VPN",
        username="vpn",
        password="1234",
        url="https://vpn.example",
        tags=["infra", "vpn"],
    )
    mgr.add_entry(
        work.uuid,
        title="API Shared A",
        username="api",
        password="same-secret-xyz",
        url="https://api.example.com",
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
        tags=["ssh"],
    )
    mgr.add_entry(
        personal.uuid,
        title="Email",
        username="me@example.com",
        password="Mailbox#Safe99",
        url="https://mail.example.com",
        notes="Personal inbox",
        tags=["personal"],
    )
    mgr.add_entry(
        personal.uuid,
        title="Empty Secret",
        username="",
        password="",
    )
    mgr.save()
    mgr.close_all()


def grab(widget, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    pix = widget.grab()
    assert not pix.isNull(), f"Failed to grab {name}"
    ok = pix.save(str(path), "PNG")
    assert ok, f"Failed to save {path}"
    print(f"saved {path} ({pix.width()}x{pix.height()})")
    if name in README_EXPORT:
        README_SHOTS.mkdir(parents=True, exist_ok=True)
        dest = README_SHOTS / README_EXPORT[name]
        shutil.copy2(path, dest)
        print(f"  → {dest.relative_to(ROOT)}")
    return path


def main() -> int:
    build_sample_db(SAMPLE)

    import json
    import os
    import tempfile

    from kdbxstudio.i18n import set_language
    from kdbxstudio.ui.dialogs.command_palette import CommandPalette, PaletteAction
    from kdbxstudio.ui.main_window import MainWindow
    from kdbxstudio.ui.theme import ThemeMode, apply_theme
    from kdbxstudio.ui.theme.scale import configure_high_dpi

    # Isolate from the developer's real settings (language/theme).
    cfg = Path(tempfile.mkdtemp(prefix="kdbxstudio-shots-"))
    (cfg / "kdbxstudio").mkdir()
    (cfg / "kdbxstudio" / "settings.json").write_text(
        json.dumps(
            {
                "version": 6,
                "language": "en",
                "theme": "dark",
                "check_updates_on_start": False,
                "start_minimized_to_tray": False,
                "browser_integration_enabled": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    os.environ["XDG_CONFIG_HOME"] = str(cfg)

    configure_high_dpi()
    set_language("en")
    app = QApplication(sys.argv)
    app.setApplicationName("KDBXStudio")
    apply_theme(app, ThemeMode.DARK, force=True)

    window = MainWindow()
    window.resize(1280, 800)
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
    work = next(g for g in window._dbm.list_groups() if g.name == "Work")
    # Root has no direct entries — select Work so the list is populated.
    window._refresh_ui()
    window._group_tree.set_groups(
        window._dbm.list_groups(),
        window._dbm.root_group_uuid(),
        select_uuid=work.uuid,
    )
    window._on_group_selected(work.uuid)
    window._show_entry(github.uuid)
    app.processEvents()
    report = window._audit.run()
    assert report.total_entries >= 6
    assert report.findings, "audit should report sample issues"
    assert window._entry_list.model().rowCount() >= 3
    grab(window, "02_workspace_open")

    # SSH entry for icon variety (dev artifact only)
    ssh = next(e for e in entries if e.title == "Deploy SSH")
    window._show_entry(ssh.uuid)
    app.processEvents()
    grab(window, "02b_ssh_entry_icons")

    window._search_box.setText("GitHub")
    window._run_search()
    app.processEvents()
    assert window._entry_list.model().rowCount() >= 1
    window._show_entry(github.uuid)
    app.processEvents()
    grab(window, "03_search_github")

    palette = CommandPalette(
        [
            PaletteAction("save", "Save", ("save",), window.save_database),
            PaletteAction(
                "add-entry", "Add Entry…", ("entry", "add"), window.add_entry
            ),
            PaletteAction(
                "generate",
                "Password Generator…",
                ("password", "generate"),
                window.open_password_generator,
            ),
            PaletteAction(
                "health",
                "Security Dashboard…",
                ("audit", "health", "security", "dashboard"),
                window.open_security_dashboard,
            ),
            PaletteAction(
                "settings",
                "Security & Appearance…",
                ("settings", "theme"),
                window.open_security_settings,
            ),
            PaletteAction(
                "lock", "Lock All", ("lock",), window._on_auto_lock
            ),
        ],
        window,
    )
    palette.show()
    app.processEvents()
    # Offscreen grabs miss mid-fade opacity; force fully opaque before capture.
    if hasattr(palette, "_fade_anim"):
        palette._fade_anim.stop()
    effect = palette.graphicsEffect()
    if effect is not None:
        effect.setOpacity(1.0)
    app.processEvents()
    grab(palette, "04_command_palette")
    palette.close()

    window.open_security_dashboard()
    app.processEvents()
    dash = window._audit_dialog
    assert dash is not None
    assert dash.view_model.snapshot is not None
    dash.resize(1280, 800)
    dash.show()
    dash.raise_()
    app.processEvents()
    grab(dash, "05_security_dashboard")
    dash.close()

    from kdbxstudio.ui.dialogs.password_generator_dialog import PasswordGeneratorDialog

    gen = PasswordGeneratorDialog(window)
    gen.show()
    app.processEvents()
    grab(gen, "06_password_generator")
    gen.close()

    _downscale_readme_shots()

    print(
        f"OK sample={SAMPLE} entries={len(entries)} "
        f"findings={len(report.findings)} "
        f"weak={report.weak_passwords} empty={report.empty_passwords} "
        f"readme_shots={README_SHOTS}"
    )
    QTimer.singleShot(50, app.quit)
    return app.exec()


def _downscale_readme_shots(*, max_width: int = 1280) -> None:
    """Keep GitHub README images reasonably sized."""
    try:
        from PIL import Image
    except ImportError:
        return
    for path in README_SHOTS.glob("*.png"):
        im = Image.open(path)
        if im.width <= max_width:
            continue
        height = int(im.height * (max_width / im.width))
        out = im.resize((max_width, height), Image.Resampling.LANCZOS)
        out.save(path, "PNG", optimize=True)
        print(f"resized {path.name} → {max_width}x{height}")


if __name__ == "__main__":
    raise SystemExit(main())
