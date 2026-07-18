"""Unlock dialog Enter key must accept, not open Browse."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox, QPushButton

from kdbxstudio.ui.dialogs.unlock_dialog import UnlockDialog


def test_browse_buttons_are_not_auto_default(qtbot, tmp_path: Path) -> None:
    db = tmp_path / "vault.kdbx"
    db.write_bytes(b"")
    dialog = UnlockDialog(None, path=db, create_mode=False)
    qtbot.addWidget(dialog)
    browse_buttons = [
        btn
        for btn in dialog.findChildren(QPushButton)
        if btn.text() in {"Browse…", "…"}
    ]
    assert browse_buttons
    for btn in browse_buttons:
        assert btn.autoDefault() is False
        assert btn.isDefault() is False
    ok = dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
    assert ok is not None
    assert ok.isDefault() is True


def test_enter_in_password_accepts_dialog(qtbot, tmp_path: Path) -> None:
    db = tmp_path / "vault.kdbx"
    db.write_bytes(b"")
    dialog = UnlockDialog(None, path=db, create_mode=False)
    qtbot.addWidget(dialog)
    dialog._password.setText("demo-pass")
    dialog._password.setFocus()
    with qtbot.waitSignal(dialog.accepted, timeout=2000):
        qtbot.keyClick(dialog._password, Qt.Key.Key_Return)
