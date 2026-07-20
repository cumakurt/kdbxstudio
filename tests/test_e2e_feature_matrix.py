"""End-to-end feature matrix against a rich sample KDBX database.

Exercises every application-layer capability with one seeded vault so
regressions surface as concrete failures rather than coverage gaps.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from kdbxstudio.application.audit_engine import AuditEngine
from kdbxstudio.application.autotype import detect_backend, expand_sequence
from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.emergency_sheet import render_emergency_html
from kdbxstudio.application.export import export_entries_csv
from kdbxstudio.application.favicon import normalize_host
from kdbxstudio.application.hibp import password_sha1
from kdbxstudio.application.history_diff import diff_history
from kdbxstudio.application.import_csv import import_entries_csv
from kdbxstudio.application.merge import merge_databases
from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.application.search_engine import EntryFilter, SearchEngine
from kdbxstudio.application.ssh_agent import agent_available
from kdbxstudio.application.templates import get_template, list_templates
from kdbxstudio.core.database import InvalidCredentialsError, KdbxDatabase
from kdbxstudio.core.password_generator import (
    GeneratorOptions,
    estimate_entropy_bits,
    generate_password,
)
from kdbxstudio.core.pem_inspector import inspect_pem_text
from kdbxstudio.core.totp import current_totp, looks_like_otp
from kdbxstudio.plugins.marketplace import get_catalog
from kdbxstudio.security.session import AutoLockController, ClipboardGuard
from kdbxstudio.security.settings import SecuritySettings
from kdbxstudio.security.store import (
    clear_recent_databases,
    load_recent_databases,
    load_settings,
    remember_database,
    save_settings,
)

OTP_URI = "otpauth://totp/Demo:user?secret=JBSWY3DPEHPK3PXP&issuer=Demo&period=30"
SAMPLE_PASSWORD = "Master#Pass99!"


def _seed_sample_vault(mgr: DatabaseManager) -> dict[str, str]:
    """Populate the active session with representative data. Returns UUID map."""
    root = mgr.root_group_uuid()
    work = mgr.add_group(root, "Work")
    banking = mgr.add_group(work.uuid, "Banking")
    personal = mgr.add_group(root, "Personal")

    github = mgr.add_entry(
        work.uuid,
        title="GitHub",
        username="dev@example.com",
        password="StrongPass!2024Xy",
        url="https://github.com/login",
        notes="## Work\n**primary account**",
        tags=["work", "dev"],
        expires=True,
        expiry_time=datetime.now(UTC) + timedelta(days=7),
        custom_properties={"Type": "Login", "Env": "prod"},
    )
    mgr.update_entry(github.uuid, otp=OTP_URI)
    mgr.add_attachment(github.uuid, "readme.txt", b"hello attachment")

    expired = mgr.add_entry(
        banking.uuid,
        title="Old Card",
        username="cardholder",
        password="Card!Pass99Long",
        tags=["finance"],
        expires=True,
        expiry_time=datetime.now(UTC) - timedelta(days=3),
    )
    mgr.add_entry(work.uuid, title="Weak VPN", username="sameuser", password="1234")
    mgr.add_entry(work.uuid, title="Empty Secret", username="sameuser", password="")
    mgr.add_entry(
        work.uuid, title="Dup A", username="sameuser", password="dup-secret-aaa"
    )
    mgr.add_entry(
        personal.uuid, title="Dup B", username="other", password="dup-secret-aaa"
    )
    mgr.add_entry(
        work.uuid,
        title="Same User Extra",
        username="sameuser",
        password="UniquePass!99",
    )
    mgr.add_entry(
        personal.uuid,
        title="Email",
        username="me@example.com",
        password="Mailbox#Safe99",
        url="https://mail.example.com",
        tags=["personal"],
    )
    ssh = mgr.add_entry(
        work.uuid,
        title="Deploy SSH",
        username="deploy",
        password="unused",
        notes=(
            "-----BEGIN OPENSSH PRIVATE KEY-----\n"
            "cHJpdmF0ZQ==\n"
            "-----END OPENSSH PRIVATE KEY-----\n"
        ),
        custom_properties={"Type": "SSH Key"},
    )
    return {
        "root": root,
        "work": work.uuid,
        "banking": banking.uuid,
        "personal": personal.uuid,
        "github": github.uuid,
        "expired": expired.uuid,
        "ssh": ssh.uuid,
    }


def test_e2e_sample_database_feature_matrix(tmp_path: Path) -> None:
    """Walk every major feature against one sample vault."""
    db_path = tmp_path / "sample.kdbx"
    key_path = tmp_path / "master.key"
    key_path.write_bytes(b"sample-keyfile-material!!")

    mgr = DatabaseManager()
    notify_count = 0

    def _on_change() -> None:
        nonlocal notify_count
        notify_count += 1

    mgr.add_listener(_on_change)

    # --- Database lifecycle (password + keyfile) ---
    sid = mgr.create(db_path, password=SAMPLE_PASSWORD, keyfile=key_path)
    assert sid.endswith("sample.kdbx")
    assert notify_count >= 1
    ids = _seed_sample_vault(mgr)
    assert mgr.any_dirty() is True
    info = mgr.database_info()
    assert info.entry_count >= 8
    assert info.group_count >= 4
    assert "unknown" not in info.version.lower() or info.version

    mgr.save()
    assert mgr.any_dirty() is False
    mgr.close()
    assert mgr.session_ids() == []

    with pytest.raises(InvalidCredentialsError):
        mgr.open(db_path, password="wrong", keyfile=key_path)

    mgr.open(db_path, password=SAMPLE_PASSWORD, keyfile=key_path)
    github = mgr.get_entry(ids["github"])
    assert github is not None
    assert github.tags == ("work", "dev")
    assert github.custom_properties.get("Env") == "prod"
    assert github.otp.startswith("otpauth://")
    assert github.expires is True

    # --- TOTP ---
    status = current_totp(github.otp)
    assert status.valid is True
    assert len(status.code) == 6
    assert looks_like_otp(github.otp) is True
    assert looks_like_otp("not-an-otp") is False

    # --- Attachments (list / save-as / delete) ---
    attachments = mgr.list_attachments(github.uuid)
    assert len(attachments) == 1
    assert attachments[0].data == b""
    assert attachments[0].size == len(b"hello attachment")
    payload = mgr.get_attachment_data(github.uuid, attachments[0].id)
    assert payload == b"hello attachment"
    save_as = tmp_path / "export" / attachments[0].filename
    save_as.parent.mkdir()
    save_as.write_bytes(payload)
    assert save_as.read_bytes() == b"hello attachment"

    # --- Groups / move / list by group ---
    work_entries = mgr.list_entries(ids["work"])
    assert any(e.title == "GitHub" for e in work_entries)
    moved = mgr.move_entry(ids["expired"], ids["work"])
    assert "Banking" not in moved.group_path
    assert "Work" in moved.group_path

    # --- History + diff + restore ---
    mgr.update_entry(
        github.uuid,
        title="GitHub Renamed",
        password="NewStrong!2025Xy",
    )
    history = mgr.list_history(github.uuid)
    assert history
    diffs = diff_history(history[0], mgr.get_entry(github.uuid))  # type: ignore[arg-type]
    assert {d.field for d in diffs} >= {"title", "password"}
    assert all("••••" in d.after or d.field != "password" for d in diffs)
    restored = mgr.restore_history(github.uuid, 0)
    assert restored.title == "GitHub"
    assert restored.password == "StrongPass!2024Xy"

    # --- Search & filters ---
    search = SearchEngine(mgr)
    github_hits = search.search(EntryFilter(query="github"))
    assert any(h.entry.title == "GitHub" for h in github_hits)
    assert any(
        h.entry.title == "Old Card"
        for h in search.search(EntryFilter(tag_contains="finance"))
    )
    assert len(search.search(EntryFilter(group_path_contains="Work"))) >= 3
    assert any(
        h.entry.title == "Old Card"
        for h in search.search(EntryFilter(expired_only=True))
    )
    assert all(
        len(h.entry.password or "") >= 12
        for h in search.search(EntryFilter(min_password_length=12))
    )
    assert any(
        h.entry.title == "GitHub"
        for h in search.search(EntryFilter(has_url=True, has_otp_or_custom=True))
    )
    assert any(
        h.entry.title.startswith("Dup")
        for h in search.search(EntryFilter(duplicates_only=True))
    )
    assert any(
        h.entry.title == "Weak VPN" for h in search.search(EntryFilter(weak_only=True))
    )

    # --- Audit before recycle mutations (incl. HIBP mock) ---
    report = AuditEngine(mgr).run()
    kinds = {f.kind for f in report.findings}
    assert "expired" in kinds
    assert "expiring_soon" in kinds
    assert "weak_password" in kinds
    assert "duplicate_password" in kinds or report.duplicates >= 1
    assert report.reused_usernames >= 1
    assert "empty_password" in kinds

    with patch(
        "kdbxstudio.application.hibp.pwned_count",
        return_value=42,
    ):
        hibp_report = AuditEngine(mgr).run(check_hibp=True, hibp_limit=5)
    assert hibp_report.pwned >= 1
    hibp_kinds = {f.kind for f in hibp_report.findings}
    assert "pwned_password" in hibp_kinds or "hibp_truncated" in hibp_kinds
    assert password_sha1("password") == "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8"

    empty = next(e for e in mgr.all_entries() if e.title == "Empty Secret")
    mgr.delete_entry(empty.uuid)
    assert any(
        h.entry.title == "Empty Secret"
        for h in search.search(EntryFilter(in_recycle_bin=True))
    )

    # --- Templates ---
    templates = list_templates()
    assert {t.id for t in templates} >= {
        "login",
        "api_key",
        "ssh_key",
        "certificate",
        "secure_note",
        "bank_card",
    }
    api_tmpl = get_template("api_key")
    assert api_tmpl is not None
    api_entry = mgr.add_entry(
        ids["root"],
        title="Service Key",
        password="sk_live_example",
        notes=api_tmpl.notes_placeholder,
        custom_properties=dict(api_tmpl.custom_defaults),
    )
    assert mgr.get_entry(api_entry.uuid).custom_properties.get("Type") == "API Key"

    # --- Password generator ---
    generated = generate_password(GeneratorOptions(length=24))
    assert len(generated) == 24
    bits = estimate_entropy_bits(generated, 70)
    assert bits > 40

    # --- Auto-Type expand ---
    steps = expand_sequence(
        "{USERNAME}{TAB}{PASSWORD}{ENTER}{TOTP}{URL}",
        username="u",
        password="p",
        totp="123456",
        url="https://example.com",
    )
    assert ("type", "u") in steps
    assert ("key", "Tab") in steps
    assert ("type", "123456") in steps
    _ = detect_backend()  # may be None in CI — still callable

    # --- PEM / SSH agent probe ---
    pem_blocks = inspect_pem_text(
        "-----BEGIN OPENSSH PRIVATE KEY-----\n"
        "cHJpdmF0ZQ==\n"
        "-----END OPENSSH PRIVATE KEY-----\n"
    )
    assert pem_blocks[0].kind == "private_key"
    _ = agent_available()

    # --- Favicon host normalize ---
    assert normalize_host("https://WWW.Example.COM/path") == "www.example.com"

    # --- CSV export / import (otp, tags, custom, expiry) ---
    csv_path = tmp_path / "vault.csv"
    export_entries_csv(
        csv_path,
        [e for e in mgr.all_entries() if not e.in_recycle_bin],
    )
    import_db = KdbxDatabase()
    import_db.create(tmp_path / "imported.kdbx", password="import")
    imported = import_entries_csv(import_db, csv_path)
    assert imported.created >= 5
    gh = next(e for e in import_db.list_entries() if e.title == "GitHub")
    assert gh.otp.startswith("otpauth://")
    assert "work" in gh.tags
    assert gh.custom_properties.get("Env") == "prod"

    # --- Merge ---
    merge_src = KdbxDatabase()
    merge_src.create(tmp_path / "merge-src.kdbx", password="s")
    merge_dst = KdbxDatabase()
    merge_dst.create(tmp_path / "merge-dst.kdbx", password="d")
    src_entry = merge_src.add_entry(
        merge_src.root_group_uuid(),
        title="Merged",
        password="secret",
        tags=["m"],
    )
    merge_src.add_attachment(src_entry.uuid, "a.bin", b"\x00\x01")
    result = merge_databases(merge_dst, merge_src)
    assert result.added == 1
    merged = next(e for e in merge_dst.list_entries() if e.title == "Merged")
    assert (
        merge_dst.get_attachment_data(
            merged.uuid, merge_dst.list_attachments(merged.uuid)[0].id
        )
        == b"\x00\x01"
    )

    # --- Emergency sheet ---
    sheet = render_emergency_html(
        [github],
        include_passwords=False,
    )
    assert "GitHub" in sheet
    assert github.password not in sheet
    assert "••••••••" in sheet

    # --- Recycle bin empty (entry + permanent deletes) ---
    removed = mgr.empty_recycle_bin()
    assert removed >= 1
    assert mgr.get_entry(empty.uuid) is None
    doomed = mgr.add_entry(ids["root"], title="Doomed", password="x")
    mgr.delete_entry(doomed.uuid, permanent=True)
    assert mgr.get_entry(doomed.uuid) is None
    temp_group = mgr.add_group(ids["root"], "TempGroup")
    mgr.add_entry(temp_group.uuid, title="Child")
    mgr.delete_group(temp_group.uuid, permanent=True)
    assert all(g.name != "TempGroup" for g in mgr.list_groups())

    # --- Change credentials (password + clear keyfile) ---
    mgr.change_credentials(password="NewMaster#Pass1")
    mgr.change_credentials(clear_keyfile=True)
    mgr.save()
    mgr.close()
    with pytest.raises(InvalidCredentialsError):
        mgr.open(db_path, password=SAMPLE_PASSWORD, keyfile=key_path)
    mgr.open(db_path, password="NewMaster#Pass1")

    # --- Multi-session save_all / close_all ---
    second = tmp_path / "second.kdbx"
    mgr.create(second, password="second")
    mgr.add_entry(mgr.root_group_uuid(), title="OnlyInSecond")
    assert len(mgr.session_ids()) == 2
    assert set(mgr.dirty_session_ids())
    saved = mgr.save_all()
    assert saved
    assert mgr.dirty_session_ids() == []
    paths = mgr.session_paths()
    assert len(paths) == 2
    mgr.close_all()
    assert mgr.session_ids() == []

    # --- Plugins discover + marketplace ---
    builtin = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "kdbxstudio"
        / "plugins"
        / "builtin"
    )
    plugins = PluginManager()
    names = plugins.discover(builtin, allow_unverified=True)
    assert (
        set(names)
        >= {
            "search-boost",
            "duplicate-highlight",
            "audit-notify",
        }
        or len(names) >= 3
    )
    plugins.activate_all()
    assert all(p.active for p in plugins.list_plugins())
    plugins.deactivate(names[0])
    assert get_catalog()

    # --- Settings / recent databases ---
    settings_path = tmp_path / "settings.json"
    recent_path = tmp_path / "recent.json"
    save_settings(
        SecuritySettings(
            clipboard_timeout_ms=3_000,
            hibp_enabled=True,
            read_only=False,
            autotype_sequence="{USERNAME}{TAB}{PASSWORD}{ENTER}",
        ),
        path=settings_path,
    )
    loaded = load_settings(path=settings_path)
    assert loaded.clipboard_timeout_ms == 3_000
    assert loaded.hibp_enabled is True
    remember_database(db_path, path=recent_path)
    assert any(str(db_path) in str(p) for p in load_recent_databases(path=recent_path))
    clear_recent_databases(path=recent_path)
    assert load_recent_databases(path=recent_path) == []

    # Save-as roundtrip
    alt = tmp_path / "save-as.kdbx"
    db = KdbxDatabase()
    db.create(tmp_path / "orig-save.kdbx", password="x")
    db.add_entry(db.root_group_uuid(), title="SavedAs")
    db.save(path=alt)
    db.close()
    db.open(alt, password="x")
    assert any(e.title == "SavedAs" for e in db.list_entries())


def test_e2e_clipboard_and_autolock_qt(qtbot) -> None:  # type: ignore[no-untyped-def]
    """Clipboard timeout clear + idle auto-lock signal."""
    app = QApplication.instance()
    assert app is not None
    store = {"value": ""}

    def _set(text: str) -> None:
        store["value"] = text

    def _clear() -> None:
        store["value"] = ""

    guard = ClipboardGuard(_set, _clear, timeout_ms=50)
    guard.copy("secret-value")
    assert store["value"] == "secret-value"
    qtbot.waitUntil(lambda: store["value"] == "", timeout=2000)

    guard.copy("again")
    assert store["value"] == "again"
    guard.cancel()
    assert store["value"] == ""

    lock = AutoLockController(idle_timeout_ms=40)
    locked = {"hit": False}
    lock.lock_requested.connect(lambda: locked.__setitem__("hit", True))
    lock.activity()
    qtbot.waitUntil(lambda: locked["hit"] is True, timeout=2000)
    lock.stop()


def test_clipboard_timeout_preserves_newer_user_content(qtbot) -> None:  # type: ignore[no-untyped-def]
    store = {"value": ""}
    clears: list[bool] = []

    def clear() -> None:
        clears.append(True)
        store["value"] = ""

    guard = ClipboardGuard(
        lambda text: store.__setitem__("value", text),
        clear,
        timeout_ms=30,
        clipboard_getter=lambda: store["value"],
    )
    guard.copy("vault-secret")
    store["value"] = "new user clipboard"
    qtbot.wait(80)
    assert store["value"] == "new user clipboard"
    assert clears == []


def test_e2e_gui_main_window_with_sample(qtbot, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """MainWindow opens a sample DB and refreshes workspace widgets."""
    from kdbxstudio.ui.main_window import MainWindow

    db_path = tmp_path / "gui-sample.kdbx"
    mgr = DatabaseManager()
    mgr.create(db_path, password=SAMPLE_PASSWORD)
    root = mgr.root_group_uuid()
    mgr.add_entry(
        root,
        title="GUI Entry",
        username="gui",
        password="GuiPass!12345",
        url="https://example.com",
        tags=["gui"],
    )
    mgr.update_entry(
        mgr.all_entries()[0].uuid,
        otp=OTP_URI,
    )
    mgr.save()
    # Keep manager open for the window — MainWindow owns its own manager.
    mgr.close()

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window._dbm.open(db_path, password=SAMPLE_PASSWORD)
    # Listener refreshes UI on open.
    assert window._dbm.active is not None
    with patch("kdbxstudio.ui.main_window.prefetch_favicons") as prefetch:
        window._prefetch_entry_favicons(["https://private.example"])
    prefetch.assert_not_called()
    entries = window._dbm.all_entries()
    assert any(e.title == "GUI Entry" for e in entries)
    window._dbm.close_all()
