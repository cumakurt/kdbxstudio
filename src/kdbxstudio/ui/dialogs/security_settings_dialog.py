"""Security settings dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QWidget,
)

from kdbxstudio.i18n import language_choices, tr
from kdbxstudio.security.settings import SecuritySettings
from kdbxstudio.ui.theme.accent import (
    ACCENT_CHOICES,
    AccentId,
    accent_label,
    accent_swatch,
    parse_accent,
)
from kdbxstudio.ui.widgets.dialog_shell import DialogShell


class _AccentSwatch(QWidget):
    """Clickable accent color chip."""

    clicked = Signal(object)  # AccentId

    def __init__(self, accent: AccentId, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.accent = accent
        self.setObjectName("accentSwatch")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tr(accent_label(accent)))
        self.setFixedSize(28, 28)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._selected = False
        self._apply_style()

    def _apply_style(self) -> None:
        color = accent_swatch(self.accent, dark=True)
        border = "#E8F0F0" if self._selected else "transparent"
        self.setStyleSheet(
            f"QWidget#accentSwatch {{ background-color: {color}; "
            f"border: 2px solid {border}; border-radius: 8px; }}"
        )

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self._apply_style()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.accent)
        super().mousePressEvent(event)


class SecuritySettingsDialog(DialogShell):
    def __init__(
        self,
        settings: SecuritySettings,
        parent: QWidget | None = None,
        *,
        on_accent_preview: object | None = None,
    ) -> None:
        super().__init__(
            parent,
            title=tr("Settings"),
            subtitle=tr("Security, appearance, and desktop preferences"),
            icon_name="settings",
            width=520,
        )
        self._original = settings
        self._accent = parse_accent(settings.accent)
        self._on_accent_preview = on_accent_preview

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

        self._hibp = QCheckBox(tr("Check passwords with HIBP"))
        self._hibp.setToolTip(
            tr("Uses the Have I Been Pwned k-anonymity password service")
        )
        self._hibp.setChecked(settings.hibp_enabled)

        self._favicons = QCheckBox(tr("Download site icons automatically"))
        self._favicons.setToolTip(
            tr("Privacy: sends entry URL domains to Google for favicon lookup")
        )
        self._favicons.setChecked(settings.favicon_downloads_enabled)
        favicon_hint = QLabel(tr("Privacy: enabled lookups send URL domains to Google"))
        favicon_hint.setObjectName("dialogSubtitle")
        favicon_hint.setWordWrap(True)
        favicon_hint.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )

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

        self._ui_scale = QComboBox()
        for pct, label in (
            (40, tr("40% — Tiny")),
            (50, tr("50% — Very small")),
            (60, tr("60% — Small")),
            (70, tr("70%")),
            (80, tr("80%")),
            (90, tr("90% — Compact")),
            (100, tr("100% — Default")),
            (110, tr("110% — Comfortable")),
            (125, tr("125% — Large")),
            (150, tr("150% — Extra large")),
        ):
            self._ui_scale.addItem(label, pct)
        scale_index = self._ui_scale.findData(settings.ui_scale_percent)
        self._ui_scale.setCurrentIndex(scale_index if scale_index >= 0 else 6)

        self._font_size = QComboBox()
        for size, label in (
            (8, tr("8 px — Tiny")),
            (9, tr("9 px")),
            (10, tr("10 px — Very small")),
            (11, tr("11 px — Small")),
            (12, tr("12 px")),
            (13, tr("13 px — Default")),
            (14, tr("14 px")),
            (15, tr("15 px")),
            (16, tr("16 px — Large")),
            (18, tr("18 px — Extra large")),
        ):
            self._font_size.addItem(label, size)
        font_index = self._font_size.findData(settings.font_size)
        self._font_size.setCurrentIndex(font_index if font_index >= 0 else 5)

        self._menu_size = QComboBox()
        self._menu_size.addItem(tr("Small"), "small")
        self._menu_size.addItem(tr("Medium — Default"), "medium")
        self._menu_size.addItem(tr("Large"), "large")
        menu_index = self._menu_size.findData(settings.menu_size)
        self._menu_size.setCurrentIndex(menu_index if menu_index >= 0 else 1)

        self._window_resolution = QComboBox()
        for key, label in (
            ("auto", tr("Auto — Fit screen")),
            ("1024x640", tr("1024 × 640 — Compact")),
            ("1280x720", tr("1280 × 720 — HD")),
            ("1280x800", tr("1280 × 800 — Default")),
            ("1440x900", tr("1440 × 900")),
            ("1600x900", tr("1600 × 900 — Large")),
            ("1920x1080", tr("1920 × 1080 — Full HD")),
        ):
            self._window_resolution.addItem(label, key)
        res_index = self._window_resolution.findData(settings.window_resolution)
        self._window_resolution.setCurrentIndex(res_index if res_index >= 0 else 0)

        accent_host = QWidget()
        accent_row = QHBoxLayout(accent_host)
        accent_row.setContentsMargins(0, 0, 0, 0)
        accent_row.setSpacing(8)
        self._swatches: list[_AccentSwatch] = []
        for accent in ACCENT_CHOICES:
            swatch = _AccentSwatch(accent, accent_host)
            swatch.set_selected(accent == self._accent)
            swatch.clicked.connect(self._select_accent)
            accent_row.addWidget(swatch)
            self._swatches.append(swatch)
        accent_row.addStretch(1)
        accent_hint = QLabel(
            tr("Tints buttons, selection, and focus across all themes")
        )
        accent_hint.setObjectName("dialogSubtitle")

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
        self._browser_install.setProperty("cssClass", "secondary")
        self._browser_install.clicked.connect(self._install_browser_host)

        form = QFormLayout()
        form.setSpacing(10)
        form.setHorizontalSpacing(16)
        form.addRow(tr("Language"), self._language)
        form.addRow(tr("Clipboard clear after"), self._clipboard)
        form.addRow(tr("Auto-lock after"), self._autolock)
        form.addRow("", self._autolock_enabled)
        form.addRow("", self._clear_on_lock)
        form.addRow("", self._minimize_on_lock)
        form.addRow("", self._hibp)
        form.addRow("", self._favicons)
        form.addRow("", favicon_hint)
        form.addRow("", self._updates)
        form.addRow("", self._tray)
        form.addRow(tr("Theme"), self._theme)
        self._import_theme = QPushButton(tr("Import custom theme…"))
        self._import_theme.setProperty("cssClass", "secondary")
        self._import_theme.clicked.connect(self._import_custom_theme)
        self._custom_theme_path = settings.custom_theme_path
        form.addRow("", self._import_theme)
        form.addRow(tr("Accent"), accent_host)
        form.addRow("", accent_hint)
        form.addRow(tr("UI density"), self._density)
        form.addRow(tr("UI scale"), self._ui_scale)
        form.addRow(tr("Font size"), self._font_size)
        form.addRow(tr("Menu size"), self._menu_size)
        form.addRow(tr("Window resolution"), self._window_resolution)
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

        form_host = QWidget()
        form_host.setLayout(form)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(form_host)
        self.body.addWidget(scroll)
        self.resize(560, 700)
        self.set_primary_text(tr("Save"))

    def _select_accent(self, accent: AccentId) -> None:
        self._accent = accent
        for swatch in self._swatches:
            swatch.set_selected(swatch.accent == accent)
        if callable(self._on_accent_preview):
            self._on_accent_preview(accent.value)

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
            accent=self._accent.value,
            read_only=self._read_only.isChecked(),
            window_geometry=self._original.window_geometry,
            window_state=self._original.window_state,
            ui_density=str(self._density.currentData()),
            ui_scale_percent=int(self._ui_scale.currentData() or 100),
            font_size=int(self._font_size.currentData() or 13),
            menu_size=str(self._menu_size.currentData() or "medium"),
            window_resolution=str(self._window_resolution.currentData() or "auto"),
            hibp_enabled=self._hibp.isChecked(),
            favicon_downloads_enabled=self._favicons.isChecked(),
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
            custom_theme_path=self._custom_theme_path,
            dashboard_hidden_panels=self._original.dashboard_hidden_panels,
        )

    def _import_custom_theme(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Import theme JSON"),
            "",
            tr("Theme JSON (*.json)"),
        )
        if not path:
            return
        try:
            from kdbxstudio.ui.theme.custom_theme import load_custom_theme_json

            load_custom_theme_json(path)
        except (OSError, ValueError, TypeError) as exc:
            QMessageBox.warning(self, tr("Import theme"), str(exc))
            return
        self._custom_theme_path = path
        index = self._theme.findData("custom")
        if index >= 0:
            self._theme.setCurrentIndex(index)
        QMessageBox.information(
            self,
            tr("Import theme"),
            tr("Custom theme loaded. Save settings to apply."),
        )
