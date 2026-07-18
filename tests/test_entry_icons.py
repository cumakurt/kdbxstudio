"""Tests for entry/field icon type detection."""

from kdbxstudio.core.database import EntryView
from kdbxstudio.ui.icons.entry_type import (
    EntryKind,
    FieldKind,
    detect_entry_kind,
    detect_entry_kind_from_view,
    field_icon,
)


def test_detect_github_as_dev() -> None:
    kind = detect_entry_kind(
        title="GitHub",
        url="https://github.com/login",
        username="dev",
    )
    assert kind is EntryKind.DEV


def test_detect_api_from_custom_type() -> None:
    kind = detect_entry_kind(
        title="Service",
        custom_properties={"Type": "API Key"},
    )
    assert kind is EntryKind.API


def test_detect_ssh_from_pem() -> None:
    notes = (
        "-----BEGIN OPENSSH PRIVATE KEY-----\n"
        "abc\n"
        "-----END OPENSSH PRIVATE KEY-----"
    )
    kind = detect_entry_kind(title="Server", notes=notes)
    assert kind is EntryKind.SSH


def test_detect_email_from_host() -> None:
    kind = detect_entry_kind(title="Inbox", url="https://mail.example.com")
    assert kind is EntryKind.EMAIL


def test_detect_from_entry_view() -> None:
    entry = EntryView(
        uuid="1",
        title="WiFi Home",
        username="",
        password="secret",
        url="",
        notes="",
        group_path="Root",
    )
    assert detect_entry_kind_from_view(entry) is EntryKind.WIFI


def test_password_icon_adapts_to_api(qtbot) -> None:
    icon_login = field_icon(FieldKind.PASSWORD, entry_kind=EntryKind.LOGIN)
    icon_api = field_icon(FieldKind.PASSWORD, entry_kind=EntryKind.API)
    assert not icon_login.isNull()
    assert not icon_api.isNull()


def test_entry_kind_uses_colorful_badge(qtbot) -> None:
    from kdbxstudio.ui.icons.entry_type import entry_kind_icon

    assert not entry_kind_icon(EntryKind.LINUX, size=18).isNull()
    assert not entry_kind_icon(EntryKind.WINDOWS, size=18).isNull()
    assert not entry_kind_icon(EntryKind.LOGIN, size=18).isNull()


def test_entry_list_icon_falls_back_to_kind(qtbot) -> None:
    from kdbxstudio.ui.icons.entry_type import entry_list_icon

    entry = EntryView(
        uuid="2",
        title="Ubuntu Box",
        username="root",
        password="x",
        url="",
        notes="",
        group_path="Root",
    )
    assert not entry_list_icon(entry, size=16).isNull()


def test_urls_missing_favicon_dedupes(tmp_path, monkeypatch) -> None:
    from kdbxstudio.application import favicon as fav_mod

    monkeypatch.setattr(fav_mod, "_CACHE_DIR", tmp_path)
    fav_mod._FAVICON_HIT.clear()
    urls = fav_mod.urls_missing_favicon(
        [
            "https://brand-example-unique.test/a",
            "https://brand-example-unique.test/b",
            "not a host!!!",
            "",
        ],
        limit=10,
    )
    assert len(urls) == 1
    assert "brand-example-unique.test" in urls[0]
