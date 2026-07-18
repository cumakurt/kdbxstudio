#!/usr/bin/env python3
"""Exercise every major feature against a fresh sample KDBX (headless-safe).

Run:
  QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/verify_features.py
"""

from __future__ import annotations

import os
import stat
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

OTP_URI = (
    "otpauth://totp/Verify:user?secret=JBSWY3DPEHPK3PXP&issuer=Verify&period=30"
)
PASSWORD = "Verify#Master99!"


def _fail(msg: str) -> None:
    raise AssertionError(msg)


def _ok(label: str) -> None:
    print(f"  OK  {label}")


def verify_core(tmp: Path) -> None:
    from kdbxstudio.application.audit_engine import AuditEngine
    from kdbxstudio.application.autotype import expand_sequence
    from kdbxstudio.application.database_manager import DatabaseManager
    from kdbxstudio.application.emergency_sheet import write_emergency_html
    from kdbxstudio.application.export import export_entries_csv
    from kdbxstudio.application.history_diff import diff_history
    from kdbxstudio.application.import_csv import import_entries_csv
    from kdbxstudio.application.merge import merge_databases
    from kdbxstudio.application.plugin_manager import PluginManager
    from kdbxstudio.application.search_engine import EntryFilter, SearchEngine
    from kdbxstudio.application.security_dashboard import SecurityDashboardAnalyzer
    from kdbxstudio.application.templates import get_template, list_templates
    from kdbxstudio.core.database import InvalidCredentialsError, KdbxDatabase
    from kdbxstudio.core.password_generator import GeneratorOptions, generate_password
    from kdbxstudio.core.pem_inspector import inspect_pem_text
    from kdbxstudio.core.totp import current_totp
    from kdbxstudio.plugins.sdk import PluginContext
    from kdbxstudio.security.audit_log import log_security_event

    print("== Core / application features ==")
    db_path = tmp / "verify.kdbx"
    key_path = tmp / "verify.key"
    key_path.write_bytes(b"verify-keyfile-bytes!!")

    mgr = DatabaseManager()
    mgr.create(db_path, password=PASSWORD, keyfile=key_path)
    root = mgr.root_group_uuid()
    work = mgr.add_group(root, "Work")
    personal = mgr.add_group(root, "Personal")

    github = mgr.add_entry(
        work.uuid,
        title="GitHub",
        username="dev@example.com",
        password="StrongPass!2024Xy",
        url="https://github.com/login",
        notes="primary",
        tags=["work", "dev"],
        expires=True,
        expiry_time=datetime.now(UTC) + timedelta(days=5),
        custom_properties={"Type": "Login"},
    )
    mgr.update_entry(github.uuid, otp=OTP_URI)
    mgr.add_attachment(github.uuid, "note.txt", b"attachment-bytes")
    mgr.add_entry(work.uuid, title="Weak", username="u", password="1234")
    mgr.add_entry(work.uuid, title="Empty", username="u", password="")
    mgr.add_entry(work.uuid, title="Dup1", password="same-secret")
    mgr.add_entry(personal.uuid, title="Dup2", password="same-secret")
    mgr.add_entry(
        work.uuid,
        title="SSH",
        notes=(
            "-----BEGIN OPENSSH PRIVATE KEY-----\n"
            "cHJpdmF0ZQ==\n"
            "-----END OPENSSH PRIVATE KEY-----\n"
        ),
        custom_properties={"Type": "SSH Key"},
    )
    mgr.save()
    _ok("create/seed/save")

    mgr.close()
    try:
        mgr.open(db_path, password="wrong", keyfile=key_path)
        _fail("wrong password should raise")
    except InvalidCredentialsError:
        pass
    mgr.open(db_path, password=PASSWORD, keyfile=key_path)
    entry = mgr.get_entry(github.uuid)
    assert entry and entry.password == "StrongPass!2024Xy"
    assert entry.otp.startswith("otpauth://")
    _ok("reopen with password+keyfile")

    meta = mgr.list_entries(work.uuid, include_secrets=False)
    assert meta and all(e.password == "" and e.otp == "" for e in meta)
    full = mgr.get_entry(github.uuid)
    assert full and full.password
    _ok("include_secrets=False on list")

    totp = current_totp(full.otp)
    assert totp.valid and len(totp.code) == 6
    _ok("TOTP")

    atts = mgr.list_attachments(github.uuid, include_data=False)
    assert len(atts) == 1 and atts[0].data == b""
    assert mgr.get_attachment_data(github.uuid, atts[0].id) == b"attachment-bytes"
    assert len(mgr.attachment_stats()) >= 1
    _ok("attachments + batch stats")

    mgr.update_entry(github.uuid, title="GitHub2", password="NewPass!2025")
    hist = mgr.list_history(github.uuid)
    assert hist
    diffs = diff_history(hist[0], mgr.get_entry(github.uuid))  # type: ignore[arg-type]
    assert any(d.field == "title" for d in diffs)
    restored = mgr.restore_history(github.uuid, 0)
    assert restored.title == "GitHub"
    _ok("history diff/restore")

    search = SearchEngine(mgr)
    assert any(h.entry.title == "GitHub" for h in search.search("github"))
    assert any(
        h.entry.title.startswith("Dup")
        for h in search.search(EntryFilter(duplicates_only=True))
    )
    assert any(
        h.entry.title == "Weak" for h in search.search(EntryFilter(weak_only=True))
    )
    _ok("search + filters")

    report = AuditEngine(mgr).run()
    kinds = {f.kind for f in report.findings}
    assert "weak_password" in kinds
    assert "empty_password" in kinds
    with patch("kdbxstudio.application.hibp.pwned_count", return_value=9):
        hibp = AuditEngine(mgr).run(check_hibp=True, hibp_limit=10)
    assert hibp.pwned >= 1
    snap = SecurityDashboardAnalyzer(mgr).run()
    assert snap.total_entries >= 6
    _ok("audit + HIBP mock + security dashboard")

    csv_path = export_entries_csv(tmp / "out.csv", mgr.all_entries(include_recycle_bin=False))
    assert "GitHub" in csv_path.read_text(encoding="utf-8")
    assert stat.S_IMODE(csv_path.stat().st_mode) == 0o600
    sheet = write_emergency_html(tmp / "sheet.html", mgr.all_entries(include_recycle_bin=False)[:3])
    assert stat.S_IMODE(sheet.stat().st_mode) == 0o600
    _ok("CSV + emergency sheet 0600")

    import_csv = tmp / "import.csv"
    import_csv.write_text(
        "title,username,password,url,notes,group\n"
        "Imported,user,Imp!Pass99,https://ex.test,n,Work/Imported\n",
        encoding="utf-8",
    )
    result = import_entries_csv(mgr.active, import_csv)  # type: ignore[arg-type]
    assert result.created >= 1
    _ok("CSV import")

    tmpl = get_template("api_key")
    assert tmpl and "api_key" in {t.id for t in list_templates()}
    mgr.add_entry(
        root,
        title="API",
        password="sk_test",
        custom_properties=dict(tmpl.custom_defaults),
    )
    _ok("templates")

    pwd = generate_password(GeneratorOptions(length=28))
    assert len(pwd) == 28
    steps = expand_sequence("{USERNAME}{TAB}{PASSWORD}", username="a", password="b")
    assert ("type", "a") in steps and ("key", "Tab") in steps
    blocks = inspect_pem_text(
        "-----BEGIN OPENSSH PRIVATE KEY-----\ncHJpdmF0ZQ==\n-----END OPENSSH PRIVATE KEY-----\n"
    )
    assert blocks and blocks[0].kind == "private_key"
    _ok("generator + autotype expand + PEM")

    empty = next(e for e in mgr.all_entries() if e.title == "Empty")
    mgr.delete_entry(empty.uuid)
    bin_uuid = mgr.recycle_bin_uuid()
    assert bin_uuid
    assert any(e.title == "Empty" for e in mgr.list_entries(bin_uuid))
    purged = mgr.empty_recycle_bin()
    assert purged >= 1
    _ok("recycle bin + empty")

    other = tmp / "other.kdbx"
    src = KdbxDatabase()
    src.create(other, password=PASSWORD)
    src.add_entry(src.root_group_uuid(), title="Merged", password="x")
    merge = merge_databases(mgr.active, src, update_existing=False)  # type: ignore[arg-type]
    assert merge.added >= 1
    src.close()
    _ok("merge")

    plugins = PluginManager(PluginContext())
    builtin = ROOT / "src" / "kdbxstudio" / "plugins" / "builtin"
    assert plugins.discover(builtin) == []
    names = plugins.discover(builtin, allow_unverified=True)
    assert len(names) >= 3
    plugins.activate_all()
    _ok("plugins fail-closed + builtin load")

    log_security_event("verify_features_ok", database=db_path.name)
    _ok("security audit log")

    mgr.change_credentials(password="NewMaster#99!")
    mgr.save()
    mgr.close()
    mgr.open(db_path, password="NewMaster#99!", keyfile=key_path)
    assert mgr.get_entry(github.uuid) is not None
    mgr.close_all()
    _ok("change master password + reopen")


def verify_gui(tmp: Path) -> None:
    import json

    from PySide6.QtWidgets import QApplication

    from kdbxstudio.application.database_manager import DatabaseManager
    from kdbxstudio.i18n import set_language
    from kdbxstudio.security.session import ClipboardGuard
    from kdbxstudio.ui.main_window import MainWindow
    from kdbxstudio.ui.theme import ThemeMode, apply_theme, parse_accent
    from kdbxstudio.ui.theme.scale import configure_high_dpi

    print("== GUI / MainWindow features ==")
    cfg = tmp / "xdg"
    (cfg / "kdbxstudio").mkdir(parents=True)
    (cfg / "kdbxstudio" / "settings.json").write_text(
        json.dumps(
            {
                "version": 6,
                "language": "en",
                "theme": "dark",
                "accent": "teal",
                "check_updates_on_start": False,
                "start_minimized_to_tray": False,
                "browser_integration_enabled": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    os.environ["XDG_CONFIG_HOME"] = str(cfg)

    sample = tmp / "gui.kdbx"
    mgr = DatabaseManager()
    mgr.create(sample, password=PASSWORD)
    root = mgr.root_group_uuid()
    g = mgr.add_group(root, "Internet")
    entry = mgr.add_entry(
        g.uuid,
        title="GitHub",
        username="u",
        password="GuiPass!12345",
        url="https://github.com",
        tags=["work"],
    )
    mgr.update_entry(
        entry.uuid,
        otp="otpauth://totp/G:u?secret=JBSWY3DPEHPK3PXP&issuer=G",
    )
    mgr.add_attachment(entry.uuid, "a.txt", b"x")
    mgr.save()
    mgr.close_all()

    configure_high_dpi()
    set_language("en")
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app, ThemeMode.DARK, accent=parse_accent("teal"), force=True)

    window = MainWindow()
    window.show()
    app.processEvents()
    window._dbm.open(sample, password=PASSWORD)
    app.processEvents()
    assert window._dbm.active is not None
    assert window._stack.currentIndex() == 1
    _ok("MainWindow open sample")

    window._refresh_ui()
    app.processEvents()
    groups = window._dbm.list_groups()
    internet = next(g for g in groups if g.name == "Internet")
    window._group_tree.set_groups(
        groups, window._dbm.root_group_uuid(), select_uuid=internet.uuid
    )
    assert window._group_tree.select_uuid(internet.uuid) is True
    window._on_group_selected(internet.uuid)
    app.processEvents()
    listed = window._entry_list.model().rowCount()
    assert listed >= 1
    # List model must not retain secrets
    for row in range(listed):
        ev = window._entry_list._model.entry_at(row)  # noqa: SLF001
        assert ev is not None
        assert ev.password == ""
        assert ev.otp == ""
    _ok("group select lists without secrets")

    window._show_entry(entry.uuid)
    app.processEvents()
    assert window._entry_detail._password.text() == "GuiPass!12345"  # noqa: SLF001
    assert window._totp.otp_value()
    assert window._attachments._list.count() >= 1  # noqa: SLF001
    _ok("entry detail + totp + attachments panels")

    window._search_box.setText("GitHub")
    window._run_search()
    app.processEvents()
    assert window._entry_list.model().rowCount() >= 1
    window._search_box.clear()
    window._run_search()
    _ok("search UI")

    store = {"v": ""}
    guard = ClipboardGuard(lambda t: store.__setitem__("v", t), lambda: store.__setitem__("v", ""), timeout_ms=0)
    guard.copy("secret")
    assert store["v"] == "secret"
    guard.cancel()
    assert store["v"] == ""
    _ok("ClipboardGuard cancel clears")

    report = window._audit.run()
    assert report.total_entries >= 1
    window.open_security_dashboard()
    app.processEvents()
    assert window._audit_dialog is not None
    window._audit_dialog.close()
    _ok("security dashboard dialog")

    csv_out = tmp / "gui-export.csv"
    from kdbxstudio.application.export import export_entries_csv

    export_entries_csv(csv_out, window._dbm.all_entries(include_recycle_bin=False))
    assert csv_out.is_file() and stat.S_IMODE(csv_out.stat().st_mode) == 0o600
    _ok("export from open session")

    # Exercise lock helpers without modal UnlockDialog.exec() (hangs offscreen).
    if window._settings.clear_clipboard_on_lock:
        window._clipboard.cancel()
    window._dbm.close_all()
    window._clear_entry_panels()
    assert window._dbm.session_ids() == []
    _ok("manual lock clears sessions and panels")

    window.close()
    app.processEvents()


def verify_browser(tmp: Path) -> None:
    import json

    from kdbxstudio.browser import crypto
    from kdbxstudio.browser.protocol import BrowserProtocol, ProtocolContext
    from kdbxstudio.core.database import KdbxDatabase

    print("== Browser protocol ==")
    db = KdbxDatabase()
    path = tmp / "browser.kdbx"
    db.create(path, password=PASSWORD)
    root = db.root_group_uuid()
    entry = db.add_entry(
        root,
        title="Site",
        username="u",
        password="p",
        url="https://example.com/login",
    )
    db.update_entry(
        entry.uuid,
        otp="otpauth://totp/S:u?secret=JBSWY3DPEHPK3PXP&issuer=S",
    )

    protocol = BrowserProtocol(
        ProtocolContext(
            get_database=lambda: db,
            get_entries=lambda: db.list_entries(include_recycle_bin=False),
            list_groups=db.list_groups,
            prompt_associate=lambda _l: "verify",
            lock_database=lambda: None,
            ensure_group_path=db.ensure_group_path,
            add_entry=lambda *a, **k: db.add_entry(*a, **k),
            update_entry=lambda *a, **k: db.update_entry(*a, **k),
            get_entry=db.get_entry,
        )
    )
    client_pk, client_sk = crypto.generate_keypair()
    client_id = "verify-client"
    nonce = crypto.random_nonce_b64()
    cpk = protocol.handle(
        {
            "action": "change-public-keys",
            "publicKey": client_pk,
            "nonce": nonce,
            "clientID": client_id,
        }
    )
    host_pk = cpk["publicKey"]
    session = protocol.sessions[client_id]

    def enc(action: str, payload: dict) -> dict:
        n = crypto.random_nonce_b64()
        plain = json.dumps({"action": action, **payload}, separators=(",", ":"))
        msg = crypto.encrypt_json(plain, n, host_pk, client_sk)
        return protocol.handle(
            {"action": action, "message": msg, "nonce": n, "clientID": client_id}
        )

    # Unassociated must fail
    denied = enc("get-totp", {"uuid": entry.uuid})
    assert denied.get("errorCode") == "8"
    _ok("browser denies totp without association")

    assoc = enc("associate", {"key": client_pk, "idKey": client_pk})
    assert "message" in assoc
    assert session.associated is True

    totp_resp = enc("get-totp", {"uuid": entry.uuid})
    body = json.loads(
        crypto.decrypt_json(totp_resp["message"], totp_resp["nonce"], host_pk, client_sk)
    )
    assert body.get("totp")
    _ok("browser get-totp after associate")

    login = enc(
        "get-logins",
        {
            "url": "https://example.com/",
            "id": "verify",
            "keys": [{"id": "verify", "key": client_pk}],
        },
    )
    login_body = json.loads(
        crypto.decrypt_json(login["message"], login["nonce"], host_pk, client_sk)
    )
    assert login_body["count"] == "1"
    empty_keys = enc(
        "get-logins",
        {"url": "https://example.com/", "keys": []},
    )
    assert empty_keys.get("errorCode") == "8"
    _ok("browser get-logins + fail-closed keys")
    db.close()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="kdbxstudio-verify-") as raw:
        tmp = Path(raw)
        try:
            verify_core(tmp)
            verify_browser(tmp)
            verify_gui(tmp)
        except Exception as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
    print("\nAll feature checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
