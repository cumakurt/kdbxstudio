"""Security settings dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.i18n import language_choices, tr
from kdbxstudio.security.settings import SecuritySettings


class SecuritySettingsDialog(QDialog):
    def __init__(
        self,
        settings: SecuritySettings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("Settings"))
        self.setModal(True)
        self._original = settings

        self._clipboard = QSpinBox()
        self._clipboard.setRange(5, 300)
        self._clipboard.setSuffix(tr(" s"))
        self._clipboard.setValue(max(1, settings.clipboard_timeout_ms // 1000))

        self._autolock = QSpinBox()
        self._autolock.setRange(1, 180)
        self._autolock.setSuffix(tr(" min"))
        self._autolock.setValue(max(1, settings.auto_lock_timeout_ms // 60_000))

        self._autolock_enabled = QCheckBox(tr("Enable idle auto-lock"))
        self._autolock_enabled.setChecked(settings.auto_lock_enabled)

        self._clear_on_lock = QCheckBox(tr("Clear clipboard on lock"))
        self._clear_on_lock.setChecked(settings.clear_clipboard_on_lock)

        self._minimize_on_lock = QCheckBox(tr("Minimize window on lock"))
        self._minimize_on_lock.setChecked(settings.minimize_on_lock)

        self._hibp = QCheckBox(
            tr("Check passwords against Have I Been Pwned (k-anonymity)")
        )
        self._hibp.setChecked(settings.hibp_enabled)

        self._updates = QCheckBox(tr("Check for updates on startup"))
        self._updates.setChecked(settings.check_updates_on_start)

        self._tray = QCheckBox(tr("Start minimized to tray"))
        self._tray.setChecked(settings.start_minimized_to_tray)

        self._language = QComboBox()
        for code, label in language_choices():
            self._language.addItem(label, code)
        lang_index = self._language.findData(settings.language)
        self._language.setCurrentIndex(lang_index if lang_index >= 0 else 0)

        self._theme = QComboBox()
        from kdbxstudio.ui.theme.tokens import THEME_CHOICES, theme_label

        for mode in THEME_CHOICES:
            self._theme.addItem(tr(theme_label(mode)), mode.value)
        index = self._theme.findData(settings.theme)
        self._theme.setCurrentIndex(index if index >= 0 else 0)

        self._density = QComboBox()
        self._density.addItem(tr("Compact"), "compact")
        self._density.addItem(tr("Comfortable"), "comfortable")
        d_index = self._density.findData(settings.ui_density)
        self._density.setCurrentIndex(d_index if d_index >= 0 else 0)

        self._read_only = QCheckBox(tr("Open databases in read-only mode"))
        self._read_only.setChecked(settings.read_only)

        self._autotype = QLineEdit(settings.autotype_sequence)
        self._autotype.setPlaceholderText("{USERNAME}{TAB}{PASSWORD}{ENTER}")
        self._autotype_match = QCheckBox(
            tr("Match Auto-Type to active window when no entry is selected")
        )
        self._autotype_match.setChecked(settings.autotype_match_window)
        self._autotype_delay = QSpinBox()
        self._autotype_delay.setRange(0, 15_000)
        self._autotype_delay.setSingleStep(100)
        self._autotype_delay.setSuffix(tr(" ms"))
        self._autotype_delay.setValue(settings.autotype_initial_delay_ms)
        self._watch_files = QCheckBox(
            tr("Watch open database files for external changes")
        )
        self._watch_files.setChecked(settings.watch_database_files)

        self._browser = QCheckBox(tr("Enable KeePassXC-Browser integration"))
        self._browser.setChecked(settings.browser_integration_enabled)
        self._browser_install = QPushButton(tr("Install browser host manifests…"))
        self._browser_install.clicked.connect(self._install_browser_host)

        form = QFormLayout()
        form.addRow(tr("Language"), self._language)
        form.addRow(tr("Clipboard clear after"), self._clipboard)
        form.addRow(tr("Auto-lock after"), self._autolock)
        form.addRow("", self._autolock_enabled)
        form.addRow("", self._clear_on_lock)
        form.addRow("", self._minimize_on_lock)
        form.addRow("", self._hibp)
        form.addRow("", self._updates)
        form.addRow("", self._tray)
        form.addRow(tr("Theme"), self._theme)
        form.addRow(tr("UI density"), self._density)
        form.addRow(tr("Auto-Type sequence"), self._autotype)
        form.addRow(tr("Auto-Type delay"), self._autotype_delay)
        form.addRow("", self._autotype_match)
        form.addRow("", self._watch_files)
        form.addRow("", self._browser)
        browser_row = QHBoxLayout()
        browser_row.addWidget(self._browser_install)
        browser_row.addStretch(1)
        form.addRow("", browser_row)
        form.addRow("", self._read_only)
        form.addRow(
            "",
            QLabel(
                tr(
                    "Hardware keys (YubiKey challenge-response) are not supported yet "
                    "by the underlying KeePass library."
                )
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

    def _install_browser_host(self) -> None:
        from kdbxstudio.browser.install_host import install

        try:
            paths = install()
        except OSError as exc:
            QMessageBox.critical(
                self,
                tr("Browser host"),
                tr("Could not install native messaging manifests:\n{err}").format(
                    err=exc
                ),
            )
            return
        listing = "\n".join(f"  {p}" for p in paths)
        QMessageBox.information(
            self,
            tr("Browser host"),
            tr(
                "Installed KeePassXC-Browser native messaging manifests:\n{paths}\n\n"
                "Unlock a database in KDBXStudio, then Connect in the extension.\n"
                "If KeePassXC is also installed, disable its browser integration "
                "to avoid conflicting manifests."
            ).format(paths=listing),
        )

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
            autotype_match_window=self._autotype_match.isChecked(),
            autotype_initial_delay_ms=self._autotype_delay.value(),
            watch_database_files=self._watch_files.isChecked(),
            browser_integration_enabled=self._browser.isChecked(),
            plugin_sha256_allowlist=self._original.plugin_sha256_allowlist,
            check_updates_on_start=self._updates.isChecked(),
            start_minimized_to_tray=self._tray.isChecked(),
            language=str(self._language.currentData() or "en"),
        )
