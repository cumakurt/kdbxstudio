#!/usr/bin/env python3
"""Create a sample KDBX, exercise MainWindow, and capture screenshots.

Dev captures go to ``artifacts/visual/`` (gitignored).
README-ready copies go to ``assets/screenshots/`` (committed).
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "visual"
README_SHOTS = ROOT / "assets" / "screenshots"
SAMPLE = OUT / "sample.kdbx"
PASSWORD = "demo-pass-123"
UPDATE_README_SHOTS = os.environ.get(
    "KDBXSTUDIO_UPDATE_README_SHOTS", "1"
).strip().lower() not in {"0", "false", "no"}

# Stable names referenced from README.md — regenerate all of these.
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

    # Named groups → colorful category icons in the Groups tree.
    internet = mgr.add_group(root, "Internet")
    windows = mgr.add_group(root, "Windows")
    linux = mgr.add_group(root, "Linux")
    cloud = mgr.add_group(root, "Cloud")
    docker = mgr.add_group(root, "Docker")
    ssh_grp = mgr.add_group(root, "SSH Keys")
    vpn = mgr.add_group(root, "VPN")
    bank = mgr.add_group(root, "Bank")
    email = mgr.add_group(root, "Email")
    personal = mgr.add_group(root, "Personal")
    work = mgr.add_group(root, "Work")

    github = mgr.add_entry(
        internet.uuid,
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
        internet.uuid,
        title="Google",
        username="dev@example.com",
        password="Mailbox#Safe99-Long",
        url="https://accounts.google.com",
        tags=["work"],
    )
    mgr.add_entry(
        internet.uuid,
        title="Microsoft 365",
        username="dev@example.com",
        password="Office#Cloud2024",
        url="https://login.microsoftonline.com",
        tags=["work"],
    )
    mgr.add_entry(
        internet.uuid,
        title="LinkedIn",
        username="dev@example.com",
        password="Linked#In2024Safe",
        url="https://www.linkedin.com",
        tags=["work"],
    )
    mgr.add_entry(
        windows.uuid,
        title="Win Server RDP",
        username="Administrator",
        password="WinSrv!Admin2024",
        url="rdp://winsrv.lab.local",
        tags=["windows", "infra"],
    )
    mgr.add_entry(
        linux.uuid,
        title="Ubuntu Host",
        username="deploy",
        password="Linux#Host99",
        url="https://ubuntu.com",
        tags=["linux"],
    )
    mgr.add_entry(
        cloud.uuid,
        title="AWS Console",
        username="admin",
        password="AwsCloud!2024-Safe",
        url="https://console.aws.amazon.com",
        tags=["cloud", "aws"],
    )
    mgr.add_entry(
        docker.uuid,
        title="Docker Hub",
        username="dev",
        password="Docker#Hub99",
        url="https://hub.docker.com",
        tags=["docker"],
    )
    mgr.add_entry(
        ssh_grp.uuid,
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
        vpn.uuid,
        title="Weak VPN",
        username="vpn",
        password="1234",
        url="https://vpn.example",
        tags=["infra", "vpn"],
    )
    mgr.add_entry(
        bank.uuid,
        title="PayPal",
        username="me@example.com",
        password="Pay#PalSafe2024",
        url="https://www.paypal.com",
        tags=["finance"],
    )
    mgr.add_entry(
        email.uuid,
        title="Proton Mail",
        username="me@example.com",
        password="Mail#Proton99",
        url="https://mail.proton.me",
        tags=["personal"],
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
        personal.uuid,
        title="Empty Secret",
        username="",
        password="",
    )
    mgr.save()
    mgr.close_all()


def _warm_favicons(urls: list[str], *, timeout_s: float = 20.0) -> int:
    """Synchronously fetch site icons so README shots show brand marks."""
    from kdbxstudio.application.favicon import cached_favicon, fetch_favicon

    deadline = time.monotonic() + timeout_s
    ok = 0
    for url in urls:
        if time.monotonic() > deadline:
            break
        if cached_favicon(url) is not None:
            ok += 1
            continue
        try:
            if fetch_favicon(url, timeout_s=5.0) is not None:
                ok += 1
        except Exception:
            pass
    return ok


def _force_opaque(widget) -> None:
    if hasattr(widget, "_fade_anim"):
        widget._fade_anim.stop()
    effect = widget.graphicsEffect()
    if effect is not None:
        effect.setOpacity(1.0)


def grab(widget, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    pix = widget.grab()
    assert not pix.isNull(), f"Failed to grab {name}"
    ok = pix.save(str(path), "PNG")
    assert ok, f"Failed to save {path}"
    print(f"saved {path} ({pix.width()}x{pix.height()})")
    if UPDATE_README_SHOTS and name in README_EXPORT:
        README_SHOTS.mkdir(parents=True, exist_ok=True)
        dest = README_SHOTS / README_EXPORT[name]
        shutil.copy2(path, dest)
        print(f"  → {dest.relative_to(ROOT)}")
    return path


def _select_group(window, name: str) -> str:
    group = next(g for g in window._dbm.list_groups() if g.name == name)
    window._group_tree.set_groups(
        window._dbm.list_groups(),
        window._dbm.root_group_uuid(),
        select_uuid=group.uuid,
    )
    window._on_group_selected(group.uuid)
    return group.uuid


def main() -> int:
    # Wipe previous README shots so every file is freshly written.
    if UPDATE_README_SHOTS and README_SHOTS.is_dir():
        for old in README_SHOTS.glob("*.png"):
            old.unlink()

    build_sample_db(SAMPLE)

    import json
    import tempfile

    from kdbxstudio.i18n import set_language, tr
    from kdbxstudio.ui.dialogs.command_palette import CommandPalette, PaletteAction
    from kdbxstudio.ui.main_window import MainWindow
    from kdbxstudio.ui.theme import ThemeMode, apply_theme, parse_accent
    from kdbxstudio.ui.theme.scale import configure_high_dpi

    cfg = Path(tempfile.mkdtemp(prefix="kdbxstudio-shots-"))
    (cfg / "kdbxstudio").mkdir()
    (cfg / "kdbxstudio" / "settings.json").write_text(
        json.dumps(
            {
                "version": 6,
                "language": "en",
                "theme": "dark",
                "accent": "teal",
                "ui_density": "comfortable",
                "ui_scale_percent": 100,
                "font_size": 13,
                "menu_size": "medium",
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
    apply_theme(
        app,
        ThemeMode.DARK,
        accent=parse_accent("teal"),
        force=True,
    )

    window = MainWindow()
    window.resize(1400, 900)
    window.show()
    app.processEvents()
    # 01 — Welcome (empty shell, accent toolbar)
    grab(window, "01_empty_dashboard")

    window._dbm.open(SAMPLE, password=PASSWORD)
    app.processEvents()
    assert window._dbm.active is not None
    assert window._stack.currentIndex() == 1

    entries = window._dbm.all_entries()
    assert len(entries) >= 12, f"expected sample entries, got {len(entries)}"
    github = next(e for e in entries if e.title == "GitHub")

    favicon_urls = sorted(
        {
            e.url
            for e in entries
            if (e.url or "").startswith("https://") and "example" not in (e.url or "")
        }
    )
    warmed = _warm_favicons(favicon_urls)
    print(f"favicons warmed: {warmed}/{len(favicon_urls)}")

    window._apply_appearance()
    window._refresh_ui()
    if window._groups_dock is not None:
        window._groups_dock.setVisible(True)
        window._groups_dock.resize(260, window._groups_dock.height())
    _select_group(window, "Internet")
    window._show_entry(github.uuid)
    window._entry_list.refresh_icons()
    for _ in range(5):
        app.processEvents()
    report = window._audit.run()
    assert report.total_entries >= 12
    assert report.findings, "audit should report sample issues"
    assert window._entry_list.model().rowCount() >= 3
    # 02 — Workspace: colorful groups + site favicons + entry detail
    grab(window, "02_workspace_open")

    # Dev-only responsive coverage at tablet and minimum supported widths.
    window.resize(900, 700)
    app.processEvents()
    grab(window, "02c_workspace_tablet")
    window.resize(640, 700)
    app.processEvents()
    grab(window, "02d_workspace_compact")
    window.resize(1400, 900)
    app.processEvents()

    # Dev-only variety shot (not in README)
    _select_group(window, "SSH Keys")
    ssh = next(e for e in entries if e.title == "Deploy SSH")
    window._show_entry(ssh.uuid)
    app.processEvents()
    grab(window, "02b_ssh_entry_icons")

    # 03 — Search with filter chips + favicon result
    _select_group(window, "Internet")
    window._search_box.setText("GitHub")
    window._run_search()
    app.processEvents()
    assert window._entry_list.model().rowCount() >= 1
    window._show_entry(github.uuid)
    window._entry_list.refresh_icons()
    app.processEvents()
    grab(window, "03_search_github")
    window._search_box.clear()
    window._run_search()
    _select_group(window, "Internet")
    window._show_entry(github.uuid)
    app.processEvents()

    # 04 — Command palette with outlined action icons
    palette = CommandPalette(
        [
            PaletteAction(
                "save", tr("Save"), ("save",), window.save_database, icon="save"
            ),
            PaletteAction(
                "add-entry",
                tr("Add Entry…"),
                ("entry", "add"),
                window.add_entry,
                icon="person_add",
            ),
            PaletteAction(
                "generate",
                tr("Password Generator…"),
                ("password", "generate"),
                window.open_password_generator,
                icon="password",
            ),
            PaletteAction(
                "health",
                tr("Security Dashboard…"),
                ("audit", "health", "security", "dashboard"),
                window.open_security_dashboard,
                icon="dashboard",
            ),
            PaletteAction(
                "settings",
                tr("Security & Appearance…"),
                ("settings", "theme", "accent"),
                window.open_security_settings,
                icon="settings",
            ),
            PaletteAction(
                "lock",
                tr("Lock All"),
                ("lock",),
                window._on_auto_lock,
                icon="lock",
            ),
            PaletteAction(
                "favicon",
                tr("Fetch Favicon"),
                ("favicon", "icon"),
                window.fetch_selected_favicon,
                icon="image",
            ),
            PaletteAction(
                "theme",
                tr("Theme: Studio Dark"),
                ("theme", "dark"),
                lambda: window.set_theme("dark"),
                icon="dark_mode",
            ),
        ],
        window,
    )
    palette.show()
    app.processEvents()
    _force_opaque(palette)
    app.processEvents()
    grab(palette, "04_command_palette")
    palette.close()

    # 05 — Security Dashboard (score, KPIs, charts)
    window.open_security_dashboard()
    app.processEvents()
    dash = window._audit_dialog
    assert dash is not None
    assert dash.view_model.snapshot is not None
    dash.resize(1320, 860)
    dash.show()
    dash.raise_()
    for _ in range(8):
        app.processEvents()
    grab(dash, "05_security_dashboard")
    dash.close()

    # 06 — Password generator (filled entropy + preset UI)
    from kdbxstudio.ui.dialogs.password_generator_dialog import PasswordGeneratorDialog

    gen = PasswordGeneratorDialog(window, clipboard_guard=window._clipboard)
    gen.resize(520, 420)
    gen.show()
    gen._regenerate()
    app.processEvents()
    grab(gen, "06_password_generator")
    gen.close()

    # Dev-only settings shot verifies the long preference form remains usable.
    from kdbxstudio.ui.dialogs.security_settings_dialog import SecuritySettingsDialog

    settings_dialog = SecuritySettingsDialog(window._settings, window)
    settings_dialog.resize(520, 600)
    settings_dialog.show()
    app.processEvents()
    grab(settings_dialog, "07_security_settings_compact")
    settings_dialog.close()

    if UPDATE_README_SHOTS:
        _downscale_readme_shots()
        missing = [
            n for n in README_EXPORT.values() if not (README_SHOTS / n).is_file()
        ]
        assert not missing, f"missing README screenshots: {missing}"

    print(
        f"OK sample={SAMPLE} entries={len(entries)} "
        f"findings={len(report.findings)} "
        f"weak={report.weak_passwords} empty={report.empty_passwords} "
        f"readme_shots_updated={UPDATE_README_SHOTS}"
    )
    QTimer.singleShot(50, app.quit)
    return app.exec()


def _downscale_readme_shots(*, max_width: int = 1280) -> None:
    """Keep GitHub README images reasonably sized."""
    try:
        from PIL import Image
    except ImportError:
        return
    for path in sorted(README_SHOTS.glob("*.png")):
        im = Image.open(path)
        if im.width <= max_width:
            print(f"keep {path.name} {im.width}x{im.height}")
            continue
        height = int(im.height * (max_width / im.width))
        out = im.resize((max_width, height), Image.Resampling.LANCZOS)
        out.save(path, "PNG", optimize=True)
        print(f"resized {path.name} → {max_width}x{height}")


if __name__ == "__main__":
    raise SystemExit(main())
