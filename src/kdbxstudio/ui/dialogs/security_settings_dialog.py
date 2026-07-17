"""Security settings dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.security.settings import SecuritySettings


class SecuritySettingsDialog(QDialog):
    def __init__(
        self,
        settings: SecuritySettings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self._original = settings

        self._clipboard = QSpinBox()
        self._clipboard.setRange(5, 300)
        self._clipboard.setSuffix(" s")
        self._clipboard.setValue(max(1, settings.clipboard_timeout_ms // 1000))

        self._autolock = QSpinBox()
        self._autolock.setRange(1, 180)
        self._autolock.setSuffix(" min")
        self._autolock.setValue(max(1, settings.auto_lock_timeout_ms // 60_000))

        self._autolock_enabled = QCheckBox("Enable idle auto-lock")
        self._autolock_enabled.setChecked(settings.auto_lock_enabled)

        self._clear_on_lock = QCheckBox("Clear clipboard on lock")
        self._clear_on_lock.setChecked(settings.clear_clipboard_on_lock)

        self._minimize_on_lock = QCheckBox("Minimize window on lock")
        self._minimize_on_lock.setChecked(settings.minimize_on_lock)

        self._hibp = QCheckBox(
            "Check passwords against Have I Been Pwned (k-anonymity)"
        )
        self._hibp.setChecked(settings.hibp_enabled)

        self._updates = QCheckBox("Check for updates on startup")
        self._updates.setChecked(settings.check_updates_on_start)

        self._tray = QCheckBox("Start minimized to tray")
        self._tray.setChecked(settings.start_minimized_to_tray)

        self._theme = QComboBox()
        self._theme.addItem("Dark", "dark")
        self._theme.addItem("Light", "light")
        self._theme.addItem("System", "system")
        index = self._theme.findData(settings.theme)
        self._theme.setCurrentIndex(index if index >= 0 else 0)

        self._density = QComboBox()
        self._density.addItem("Compact", "compact")
        self._density.addItem("Comfortable", "comfortable")
        d_index = self._density.findData(settings.ui_density)
        self._density.setCurrentIndex(d_index if d_index >= 0 else 0)

        self._read_only = QCheckBox("Open databases in read-only mode")
        self._read_only.setChecked(settings.read_only)

        self._autotype = QLineEdit(settings.autotype_sequence)
        self._autotype.setPlaceholderText("{USERNAME}{TAB}{PASSWORD}{ENTER}")

        form = QFormLayout()
        form.addRow("Clipboard clear after", self._clipboard)
        form.addRow("Auto-lock after", self._autolock)
        form.addRow("", self._autolock_enabled)
        form.addRow("", self._clear_on_lock)
        form.addRow("", self._minimize_on_lock)
        form.addRow("", self._hibp)
        form.addRow("", self._updates)
        form.addRow("", self._tray)
        form.addRow("Theme", self._theme)
        form.addRow("UI density", self._density)
        form.addRow("Auto-Type sequence", self._autotype)
        form.addRow("", self._read_only)
        form.addRow(
            "",
            QLabel(
                "Hardware keys (YubiKey challenge-response) are not supported yet "
                "by the underlying KeePass library."
            ),
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def result_settings(self) -> SecuritySettings:
        return SecuritySettings(
            clipboard_timeout_ms=self._clipboard.value() * 1000,
            auto_lock_timeout_ms=self._autolock.value() * 60_000,
            auto_lock_enabled=self._autolock_enabled.isChecked(),
            clear_clipboard_on_lock=self._clear_on_lock.isChecked(),
            minimize_on_lock=self._minimize_on_lock.isChecked(),
            theme=str(self._theme.currentData()),
            read_only=self._read_only.isChecked(),
            window_geometry=self._original.window_geometry,
            window_state=self._original.window_state,
            ui_density=str(self._density.currentData()),
            hibp_enabled=self._hibp.isChecked(),
            autotype_sequence=self._autotype.text().strip()
            or SecuritySettings.autotype_sequence,
            check_updates_on_start=self._updates.isChecked(),
            start_minimized_to_tray=self._tray.isChecked(),
        )
