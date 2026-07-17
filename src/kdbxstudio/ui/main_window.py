"""Main application window."""

from __future__ import annotations

from base64 import b64decode, b64encode
from importlib import resources
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QGuiApplication,
    QIcon,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio import __version__
from kdbxstudio.application.audit_engine import AuditEngine
from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.export import export_entries_csv
from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.application.search_engine import EntryFilter, SearchEngine
from kdbxstudio.core.database import DatabaseError, InvalidCredentialsError
from kdbxstudio.security.session import AutoLockController, ClipboardGuard
from kdbxstudio.security.store import (
    clear_recent_databases,
    load_recent_databases,
    load_settings,
    remember_database,
    save_settings,
)
from kdbxstudio.ui.dialogs.change_credentials_dialog import ChangeCredentialsDialog
from kdbxstudio.ui.dialogs.command_palette import CommandPalette, PaletteAction
from kdbxstudio.ui.dialogs.database_properties_dialog import DatabasePropertiesDialog
from kdbxstudio.ui.dialogs.password_generator_dialog import PasswordGeneratorDialog
from kdbxstudio.ui.dialogs.plugin_dialog import PluginDialog
from kdbxstudio.ui.dialogs.plugin_marketplace_dialog import PluginMarketplaceDialog
from kdbxstudio.ui.dialogs.security_settings_dialog import SecuritySettingsDialog
from kdbxstudio.ui.dialogs.template_dialog import TemplateDialog
from kdbxstudio.ui.dialogs.unlock_dialog import UnlockDialog
from kdbxstudio.ui.icons import (
    ICON_ADD,
    ICON_AUDIT,
    ICON_LOCK,
    ICON_OPEN,
    ICON_PALETTE,
    ICON_PLUGIN,
    ICON_SAVE,
    icon_tool_button,
)
from kdbxstudio.ui.theme import (
    ThemeMode,
    apply_theme,
    refresh_theme_for_screen,
    suggested_window_size,
)
from kdbxstudio.ui.theme.scale import detect_ui_scale
from kdbxstudio.ui.widgets.attachment_preview import AttachmentPreviewWidget
from kdbxstudio.ui.widgets.audit_dashboard import AuditDashboardWidget
from kdbxstudio.ui.widgets.empty_workspace import EmptyWorkspaceWidget
from kdbxstudio.ui.widgets.entry_detail import EntryDetailWidget
from kdbxstudio.ui.widgets.entry_list import EntryListWidget
from kdbxstudio.ui.widgets.filter_bar import FilterBarWidget
from kdbxstudio.ui.widgets.group_tree import GroupTreeWidget
from kdbxstudio.ui.widgets.history_widget import HistoryWidget
from kdbxstudio.ui.widgets.pem_inspector import PemInspectorWidget
from kdbxstudio.ui.widgets.totp_widget import TotpWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"KDBXStudio {__version__}")
        self._apply_window_icon()
        self._main_toolbar: QToolBar | None = None
        self._settings = load_settings()

        self._dbm = DatabaseManager()
        self._search = SearchEngine(self._dbm)
        self._audit = AuditEngine(self._dbm)
        self._plugins = PluginManager()
        self._load_builtin_plugins()
        self._search.set_rank_emitter(self._plugins.context.emit)
        self._fit_to_screen(initial=True)
        self._updating_tabs = False
        self._current_entry_uuid: str | None = None
        self._active_filter = EntryFilter()
        self._recent_menu: QMenu | None = None
        self._default_geometry = QByteArray()
        self._default_state = QByteArray()

        clipboard = QGuiApplication.clipboard()
        assert clipboard is not None
        self._clipboard = ClipboardGuard(
            clipboard_setter=clipboard.setText,
            clipboard_clear=lambda: clipboard.clear(),
            timeout_ms=self._settings.clipboard_timeout_ms,
            parent=self,
        )
        self._auto_lock = AutoLockController(
            idle_timeout_ms=self._settings.auto_lock_timeout_ms,
            parent=self,
        )
        self._auto_lock.lock_requested.connect(self._on_auto_lock)
        self._auto_lock.set_enabled(self._settings.auto_lock_enabled)

        self._db_tabs = QTabWidget()
        self._db_tabs.setTabsClosable(True)
        self._db_tabs.setDocumentMode(True)
        self._db_tabs.currentChanged.connect(self._on_tab_changed)
        self._db_tabs.tabCloseRequested.connect(self._on_tab_close)

        self._group_tree = GroupTreeWidget()
        self._entry_list = EntryListWidget()
        self._entry_detail = EntryDetailWidget()
        self._history = HistoryWidget()
        self._attachments = AttachmentPreviewWidget()
        self._pem = PemInspectorWidget()
        self._totp = TotpWidget()
        self._audit_dash = AuditDashboardWidget()
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search entries…")
        self._search_box.setAccessibleName("Universal search")
        self._search_box.setClearButtonEnabled(True)
        self._search_box.returnPressed.connect(self._run_search)
        self._filter_bar = FilterBarWidget()
        self._filter_bar.filter_changed.connect(self._on_filter_changed)

        self._entry_tabs = QTabWidget()
        self._entry_tabs.addTab(self._entry_detail, "Entry")
        self._entry_tabs.addTab(self._totp, "TOTP")
        self._entry_tabs.addTab(self._history, "History")
        self._entry_tabs.addTab(self._attachments, "Attachments")
        self._entry_tabs.addTab(self._pem, "Certificates / SSH")

        workspace = QWidget()
        center_layout = QVBoxLayout(workspace)
        center_layout.setContentsMargins(6, 2, 6, 2)
        center_layout.setSpacing(2)
        self._db_tabs.setMaximumHeight(28)
        center_layout.addWidget(self._db_tabs)
        center_layout.addWidget(self._search_box)
        center_layout.addWidget(self._filter_bar)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(4)
        splitter.addWidget(self._entry_list)
        splitter.addWidget(self._entry_tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([360, 560])
        self._workspace_splitter = splitter
        center_layout.addWidget(splitter, stretch=1)

        self._empty = EmptyWorkspaceWidget()
        self._empty.open_requested.connect(self.open_database)
        self._empty.create_requested.connect(self.create_database)
        self._empty.palette_requested.connect(self.open_command_palette)
        self._empty.recent_requested.connect(self._open_recent)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._empty)
        self._stack.addWidget(workspace)
        self.setCentralWidget(self._stack)
        self._setup_docks()
        self._build_menus()
        self._build_toolbar()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        self._group_tree.group_selected.connect(self._on_group_selected)
        self._entry_list.entry_selected.connect(self._on_entry_selected)
        self._entry_detail.save_requested.connect(self._on_save_entry)
        self._entry_detail.copy_password_requested.connect(self._on_copy_password)
        self._entry_detail.generate_password_requested.connect(
            self.open_password_generator
        )
        self._history.restore_requested.connect(self._restore_history)
        self._totp.copy_requested.connect(self._on_copy_password)
        self._attachments.add_requested.connect(self._add_attachment)
        self._attachments.delete_requested.connect(self._delete_attachment)
        self._audit_dash.refresh_requested.connect(self._refresh_audit)
        self._audit_dash.finding_activated.connect(self._on_finding_activated)
        self._dbm.add_listener(self._refresh_ui)

        self._bind_shortcuts()
        self._default_geometry = self.saveGeometry()
        self._default_state = self.saveState()
        self._restore_layout()
        self._empty.set_recent(load_recent_databases())
        self._apply_chrome_scale()
        self._connect_screen_signals()
        # Start with docks hidden until a database is open.
        self._groups_dock.hide()
        self._audit_dock.hide()
        self._auto_lock.activity()

    def _bind_shortcuts(self) -> None:
        for seq in ("Ctrl+K", "Ctrl+Shift+P"):
            shortcut = QShortcut(QKeySequence(seq), self)
            shortcut.activated.connect(self.open_command_palette)

        focus_search = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_search.activated.connect(self._focus_search)

    def _focus_search(self) -> None:
        self._stack.setCurrentIndex(1 if self._dbm.active else 0)
        if self._dbm.active is not None:
            self._search_box.setFocus()
            self._search_box.selectAll()

    def _load_builtin_plugins(self) -> None:
        modules = (
            "kdbxstudio.plugins.builtin.duplicate_highlight_plugin",
            "kdbxstudio.plugins.builtin.audit_notify_plugin",
            "kdbxstudio.plugins.builtin.search_boost_plugin",
        )
        for module_name in modules:
            try:
                module = __import__(module_name, fromlist=["create_plugin"])
                self._plugins.register(module.create_plugin())
            except Exception:
                continue
        try:
            builtin = resources.files("kdbxstudio.plugins.builtin")
            root = Path(str(builtin))
            if root.is_dir():
                self._plugins.discover(root)
        except (TypeError, ModuleNotFoundError, OSError):
            pass
        self._plugins.activate_all()

    def _setup_docks(self) -> None:
        groups_dock = QDockWidget("Groups", self)
        groups_dock.setObjectName("groupsDock")
        groups_dock.setWidget(self._group_tree)
        groups_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        groups_dock.setMinimumWidth(140)
        groups_dock.setMaximumWidth(280)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, groups_dock)

        audit_dock = QDockWidget("Password Health", self)
        audit_dock.setObjectName("auditDock")
        audit_dock.setWidget(self._audit_dash)
        audit_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )
        audit_dock.setMinimumHeight(80)
        audit_dock.setMaximumHeight(180)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, audit_dock)
        self._groups_dock = groups_dock
        self._audit_dock = audit_dock
        self.resizeDocks([groups_dock], [170], Qt.Orientation.Horizontal)
        self.resizeDocks([audit_dock], [110], Qt.Orientation.Vertical)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("Open…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_database)
        file_menu.addAction(open_action)

        create_action = QAction("New Database…", self)
        create_action.setShortcut(QKeySequence.StandardKey.New)
        create_action.triggered.connect(self.create_database)
        file_menu.addAction(create_action)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_database)
        file_menu.addAction(save_action)

        export_action = QAction("Export CSV…", self)
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)

        import_action = QAction("Import CSV…", self)
        import_action.triggered.connect(self.import_csv)
        file_menu.addAction(import_action)

        props_action = QAction("Database Properties…", self)
        props_action.triggered.connect(self.show_database_properties)
        file_menu.addAction(props_action)

        creds_action = QAction("Change Master Password…", self)
        creds_action.triggered.connect(self.change_master_password)
        file_menu.addAction(creds_action)

        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close_database)
        file_menu.addAction(close_action)

        self._recent_menu = file_menu.addMenu("Open Recent")
        self._rebuild_recent_menu()

        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        entry_menu = self.menuBar().addMenu("&Entry")
        add_action = QAction("Add Entry…", self)
        add_action.triggered.connect(self.add_entry)
        entry_menu.addAction(add_action)

        template_action = QAction("New from Template…", self)
        template_action.triggered.connect(self.add_entry_from_template)
        entry_menu.addAction(template_action)

        delete_action = QAction("Move to Recycle Bin", self)
        delete_action.setShortcut(QKeySequence(Qt.Key.Key_Delete))
        delete_action.triggered.connect(lambda: self.delete_entry(False))
        entry_menu.addAction(delete_action)

        purge_action = QAction("Delete Permanently", self)
        purge_action.triggered.connect(lambda: self.delete_entry(True))
        entry_menu.addAction(purge_action)

        group_menu = self.menuBar().addMenu("&Group")
        add_group = QAction("Add Group…", self)
        add_group.triggered.connect(self.add_group)
        group_menu.addAction(add_group)
        rename_group = QAction("Rename Group…", self)
        rename_group.setShortcut(QKeySequence(Qt.Key.Key_F2))
        rename_group.triggered.connect(self.rename_group)
        group_menu.addAction(rename_group)
        delete_group = QAction("Move Group to Recycle Bin", self)
        delete_group.triggered.connect(self.delete_group)
        group_menu.addAction(delete_group)

        tools_menu = self.menuBar().addMenu("&Tools")
        audit_action = QAction("Refresh Password Audit", self)
        audit_action.triggered.connect(self._refresh_audit)
        tools_menu.addAction(audit_action)

        empty_bin = QAction("Empty Recycle Bin…", self)
        empty_bin.triggered.connect(self.empty_recycle_bin)
        tools_menu.addAction(empty_bin)

        plugins_menu = tools_menu.addMenu("Plugin Center")
        plugins_action = QAction("Marketplace…", self)
        plugins_action.triggered.connect(self.open_plugins)
        plugins_menu.addAction(plugins_action)

        plugins_mgr = QAction("Installed Plugins…", self)
        plugins_mgr.triggered.connect(self.open_installed_plugins)
        plugins_menu.addAction(plugins_mgr)

        generator_action = QAction("Password Generator…", self)
        generator_action.triggered.connect(self.open_password_generator)
        tools_menu.addAction(generator_action)

        tools_menu.addSeparator()
        lock_action = QAction("Lock All Databases", self)
        lock_action.setShortcut(QKeySequence("Ctrl+L"))
        lock_action.triggered.connect(self._on_auto_lock)
        tools_menu.addAction(lock_action)

        security_action = QAction("Settings…", self)
        security_action.triggered.connect(self.open_security_settings)
        tools_menu.addAction(security_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self._groups_dock.toggleViewAction())
        view_menu.addAction(self._audit_dock.toggleViewAction())
        view_menu.addSeparator()
        save_layout = QAction("Save Layout", self)
        save_layout.triggered.connect(self.save_layout)
        view_menu.addAction(save_layout)
        reset_layout = QAction("Reset Layout", self)
        reset_layout.triggered.connect(self.reset_layout)
        view_menu.addAction(reset_layout)
        view_menu.addSeparator()
        theme_menu = view_menu.addMenu("Theme")
        for label, value in (
            ("Dark", "dark"),
            ("Light", "light"),
            ("System", "system"),
        ):
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, v=value: self.set_theme(v))
            theme_menu.addAction(action)
        palette_action = QAction("Command Palette…", self)
        palette_action.setShortcut(QKeySequence("Ctrl+K"))
        palette_action.triggered.connect(self.open_command_palette)
        view_menu.addAction(palette_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        self._main_toolbar = toolbar

        def add_icon(name: str, tip: str, slot: object) -> None:
            button = icon_tool_button(name, tip, toolbar, size=16)
            button.clicked.connect(slot)
            toolbar.addWidget(button)

        add_icon(ICON_OPEN, "Open database", self.open_database)
        add_icon(ICON_SAVE, "Save database", self.save_database)
        add_icon(ICON_ADD, "Add entry", self.add_entry)
        add_icon(ICON_PALETTE, "Command palette", self.open_command_palette)
        add_icon(ICON_AUDIT, "Refresh password audit", self._refresh_audit)
        add_icon(ICON_PLUGIN, "Plugin marketplace", self.open_plugins)
        add_icon(ICON_LOCK, "Lock all databases", self._on_auto_lock)

    def _apply_window_icon(self) -> None:
        candidates = [
            Path(__file__).resolve().parents[3] / "assets" / "kdbxstudio.png",
            Path(__file__).resolve().parents[3] / "assets" / "kdbxstudio.svg",
        ]
        for path in candidates:
            if path.is_file():
                self.setWindowIcon(QIcon(str(path)))
                return

    def _rebuild_recent_menu(self) -> None:
        if self._recent_menu is None:
            return
        self._recent_menu.clear()
        recent = load_recent_databases()
        if not recent:
            empty = QAction("No recent databases", self)
            empty.setEnabled(False)
            self._recent_menu.addAction(empty)
        else:
            for path in recent:
                action = QAction(str(path), self)
                action.triggered.connect(
                    lambda checked=False, p=path: self._open_recent(p)
                )
                self._recent_menu.addAction(action)
        self._recent_menu.addSeparator()
        clear_action = QAction("Clear Recent", self)
        clear_action.triggered.connect(self._clear_recent)
        self._recent_menu.addAction(clear_action)

    def _open_recent(self, path: Path) -> None:
        if not path.is_file():
            QMessageBox.warning(
                self, "Missing file", f"Database no longer exists:\n{path}"
            )
            self._rebuild_recent_menu()
            return
        dialog = UnlockDialog(self, path=path, create_mode=False)
        if dialog.exec() != UnlockDialog.DialogCode.Accepted:
            return
        try:
            self._dbm.open(
                dialog.database_path(),
                password=dialog.password(),
                keyfile=dialog.keyfile(),
            )
            remember_database(dialog.database_path())
            self._rebuild_recent_menu()
            self.statusBar().showMessage(f"Opened {path.name}", 5000)
        except InvalidCredentialsError:
            QMessageBox.critical(self, "Unlock failed", "Invalid password or key file.")
        except DatabaseError as exc:
            QMessageBox.critical(self, "Open failed", str(exc))
        self._auto_lock.activity()

    def _clear_recent(self) -> None:
        clear_recent_databases()
        self._rebuild_recent_menu()
        self._empty.set_recent([])

    def import_csv(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, "Import", "Open a database first.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import CSV",
            str(Path.home()),
            "CSV Files (*.csv)",
        )
        if not path:
            return
        try:
            result = self._dbm.import_csv(path)
            self.statusBar().showMessage(
                f"Imported {result.created} entries "
                f"({result.skipped} skipped, "
                f"{result.groups_created} groups created)",
                6000,
            )
        except (OSError, DatabaseError, KeyError) as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
        self._auto_lock.activity()

    def change_master_password(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, "Credentials", "Open a database first.")
            return
        dialog = ChangeCredentialsDialog(self)
        if dialog.exec() != ChangeCredentialsDialog.DialogCode.Accepted:
            return
        try:
            self._dbm.change_credentials(
                password=dialog.password(),
                keyfile=dialog.keyfile(),
                clear_keyfile=dialog.clear_keyfile(),
            )
            self._dbm.save()
            self.statusBar().showMessage(
                "Master credentials updated and database saved", 5000
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, "Credential change failed", str(exc))
        self._auto_lock.activity()

    def add_group(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, "Add group", "Open a database first.")
            return
        parent = (
            self._group_tree.selected_group_uuid() or self._dbm.root_group_uuid()
        )
        name, ok = QInputDialog.getText(self, "New Group", "Group name:")
        if not ok or not name.strip():
            return
        try:
            group = self._dbm.add_group(parent, name.strip())
            self.statusBar().showMessage(f"Added group '{group.name}'", 3000)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Add group failed", str(exc))
        self._auto_lock.activity()

    def rename_group(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            return
        group_uuid = self._group_tree.selected_group_uuid()
        if not group_uuid:
            return
        name, ok = QInputDialog.getText(self, "Rename Group", "New name:")
        if not ok or not name.strip():
            return
        try:
            group = self._dbm.rename_group(group_uuid, name.strip())
            self.statusBar().showMessage(f"Renamed group to '{group.name}'", 3000)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Rename failed", str(exc))
        self._auto_lock.activity()

    def delete_group(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            return
        group_uuid = self._group_tree.selected_group_uuid()
        if not group_uuid:
            return
        confirm = QMessageBox.question(
            self,
            "Recycle Bin",
            "Move the selected group to the Recycle Bin?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self._dbm.delete_group(group_uuid)
            self.statusBar().showMessage("Group moved to Recycle Bin", 3000)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Delete group failed", str(exc))
        self._auto_lock.activity()

    def export_csv(self) -> None:
        if self._dbm.active is None:
            QMessageBox.information(self, "Export", "Open a database first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            str(Path.home() / "kdbxstudio-export.csv"),
            "CSV Files (*.csv)",
        )
        if not path:
            return
        confirm = QMessageBox.warning(
            self,
            "Export includes secrets",
            "The CSV file will contain passwords and OTP secrets "
            "in plain text. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            entries = self._dbm.all_entries(include_recycle_bin=False)
            export_entries_csv(path, entries)
            self.statusBar().showMessage(f"Exported {len(entries)} entries", 5000)
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
        self._auto_lock.activity()

    def show_database_properties(self) -> None:
        if self._dbm.active is None:
            QMessageBox.information(self, "Properties", "Open a database first.")
            return
        dialog = DatabasePropertiesDialog(self._dbm.database_info(), self)
        dialog.exec()

    def _restore_history(self, history_index: int) -> None:
        if not self._ensure_writable():
            return
        if not self._current_entry_uuid:
            return
        confirm = QMessageBox.question(
            self,
            "Restore revision",
            "Restore this historical revision? "
            "Current values are saved to history first.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            entry = self._dbm.restore_history(self._current_entry_uuid, history_index)
            self._show_entry(entry.uuid)
            self.statusBar().showMessage(
                "Revision restored (save database to persist)", 4000
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, "Restore failed", str(exc))
        self._auto_lock.activity()

    def open_password_generator(self) -> None:
        dialog = PasswordGeneratorDialog(self)
        if dialog.exec() != PasswordGeneratorDialog.DialogCode.Accepted:
            return
        password = dialog.password()
        if self._current_entry_uuid:
            self._entry_detail.set_password(password)
            self.statusBar().showMessage(
                "Generated password applied to entry (save to keep)", 4000
            )
        else:
            self._clipboard.copy(password)
            self.statusBar().showMessage(
                "Generated password copied to clipboard", 4000
            )
        self._auto_lock.activity()

    def set_theme(self, theme: str) -> None:
        self._settings = self._settings.with_updates(theme=theme)
        save_settings(self._settings)
        app = QApplication.instance()
        if isinstance(app, QApplication):
            try:
                mode = ThemeMode(theme)
            except ValueError:
                mode = ThemeMode.DARK
            apply_theme(app, mode)
        self.statusBar().showMessage(f"Theme: {theme}", 2000)

    def open_command_palette(self) -> None:
        actions = [
            PaletteAction(
                "open", "Open Database…", ("file", "open"), self.open_database
            ),
            PaletteAction(
                "new", "New Database…", ("create", "new"), self.create_database
            ),
            PaletteAction("save", "Save", ("save",), self.save_database),
            PaletteAction("lock", "Lock All", ("lock", "security"), self._on_auto_lock),
            PaletteAction(
                "add-entry", "Add Entry…", ("entry", "add"), self.add_entry
            ),
            PaletteAction(
                "template",
                "New from Template…",
                ("template",),
                self.add_entry_from_template,
            ),
            PaletteAction(
                "generate",
                "Password Generator…",
                ("password", "generate"),
                self.open_password_generator,
            ),
            PaletteAction(
                "audit", "Refresh Audit", ("audit", "health"), self._refresh_audit
            ),
            PaletteAction(
                "import", "Import CSV…", ("import", "csv"), self.import_csv
            ),
            PaletteAction(
                "export", "Export CSV…", ("export", "csv"), self.export_csv
            ),
            PaletteAction(
                "plugins",
                "Plugin Marketplace…",
                ("plugin", "market"),
                self.open_plugins,
            ),
            PaletteAction(
                "settings",
                "Security & Appearance…",
                ("settings", "theme"),
                self.open_security_settings,
            ),
            PaletteAction(
                "theme-dark",
                "Theme: Dark",
                ("theme", "dark"),
                lambda: self.set_theme("dark"),
            ),
            PaletteAction(
                "theme-light",
                "Theme: Light",
                ("theme", "light"),
                lambda: self.set_theme("light"),
            ),
            PaletteAction(
                "theme-system",
                "Theme: System",
                ("theme", "system"),
                lambda: self.set_theme("system"),
            ),
            PaletteAction(
                "focus-search",
                "Focus Search",
                ("search", "find"),
                lambda: self._search_box.setFocus(),
            ),
        ]
        for path in load_recent_databases()[:8]:

            def _open(p: Path = path) -> None:
                self._open_recent(p)

            actions.append(
                PaletteAction(
                    f"recent:{path}",
                    f"Open Recent: {path.name}",
                    ("recent", path.name.lower()),
                    _open,
                    section="Recent",
                )
            )
        dialog = CommandPalette(actions, self)
        dialog.exec()
        self._auto_lock.activity()

    def open_database(self) -> None:
        dialog = UnlockDialog(self, create_mode=False)
        if dialog.exec() != UnlockDialog.DialogCode.Accepted:
            return
        try:
            self._dbm.open(
                dialog.database_path(),
                password=dialog.password(),
                keyfile=dialog.keyfile(),
            )
            remember_database(dialog.database_path())
            self._rebuild_recent_menu()
            self.statusBar().showMessage(
                f"Opened {dialog.database_path().name}", 5000
            )
        except InvalidCredentialsError:
            QMessageBox.critical(self, "Unlock failed", "Invalid password or key file.")
        except DatabaseError as exc:
            QMessageBox.critical(self, "Open failed", str(exc))
        self._auto_lock.activity()

    def create_database(self) -> None:
        dialog = UnlockDialog(self, create_mode=True)
        if dialog.exec() != UnlockDialog.DialogCode.Accepted:
            return
        try:
            self._dbm.create(
                dialog.database_path(),
                password=dialog.password(),
                keyfile=dialog.keyfile(),
            )
            remember_database(dialog.database_path())
            self._rebuild_recent_menu()
            self.statusBar().showMessage(
                f"Created {dialog.database_path().name}", 5000
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, "Create failed", str(exc))
        self._auto_lock.activity()

    def _ensure_writable(self) -> bool:
        if self._settings.read_only:
            QMessageBox.information(
                self,
                "Read-only mode",
                "This session is read-only. Disable it in Security & Appearance.",
            )
            return False
        return True

    def save_database(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, "Save", "No database is open.")
            return
        try:
            self._dbm.save()
            self.statusBar().showMessage("Database saved", 3000)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
        self._auto_lock.activity()

    def close_database(self) -> None:
        self._dbm.close()
        self._clear_entry_panels()
        self.statusBar().showMessage("Database closed", 3000)

    def add_entry(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, "Add entry", "Open a database first.")
            return
        group_uuid = self._group_tree.selected_group_uuid()
        if not group_uuid:
            group_uuid = self._dbm.root_group_uuid()
        title, ok = QInputDialog.getText(self, "New Entry", "Title:")
        if not ok or not title.strip():
            return
        try:
            entry = self._dbm.add_entry(group_uuid, title=title.strip())
            self._on_group_selected(group_uuid)
            self._show_entry(entry.uuid)
            self.statusBar().showMessage(f"Added entry '{entry.title}'", 3000)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Add failed", str(exc))
        self._auto_lock.activity()

    def add_entry_from_template(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, "Template", "Open a database first.")
            return
        dialog = TemplateDialog(self)
        if dialog.exec() != TemplateDialog.DialogCode.Accepted:
            return
        template = dialog.selected_template()
        fields = dialog.field_values()
        group_uuid = (
            self._group_tree.selected_group_uuid() or self._dbm.root_group_uuid()
        )
        try:
            entry = self._dbm.add_entry(
                group_uuid,
                title=dialog.title_value(),
                username=fields.get("username", ""),
                password=fields.get("password", ""),
                url=fields.get("url", ""),
                notes=dialog.notes_value(),
            )
            if template.custom_defaults:
                self._dbm.update_entry(
                    entry.uuid,
                    custom_properties=dict(template.custom_defaults),
                )
                entry = self._dbm.get_entry(entry.uuid) or entry
            self._on_group_selected(group_uuid)
            self._show_entry(entry.uuid)
            self.statusBar().showMessage(
                f"Created '{entry.title}' from {template.name}", 4000
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, "Template failed", str(exc))
        self._auto_lock.activity()

    def delete_entry(self, permanent: bool = False) -> None:
        if not self._ensure_writable():
            return
        uuid = self._entry_list.selected_entry_uuid()
        if not uuid or self._dbm.active is None:
            return
        if permanent:
            confirm = QMessageBox.question(
                self,
                "Delete permanently",
                "Permanently delete the selected entry?",
            )
        else:
            confirm = QMessageBox.question(
                self,
                "Recycle Bin",
                "Move the selected entry to the Recycle Bin?",
            )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self._dbm.delete_entry(uuid, permanent=permanent)
            self._clear_entry_panels()
            group_uuid = self._group_tree.selected_group_uuid()
            if group_uuid:
                self._on_group_selected(group_uuid)
            self._refresh_audit()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Delete failed", str(exc))
        self._auto_lock.activity()

    def empty_recycle_bin(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            return
        confirm = QMessageBox.question(
            self,
            "Empty Recycle Bin",
            "Permanently delete all recycled entries?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            count = self._dbm.empty_recycle_bin()
            self.statusBar().showMessage(
                f"Removed {count} recycled entr(y/ies)", 4000
            )
            self._refresh_audit()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Empty bin failed", str(exc))
        self._auto_lock.activity()

    def open_security_settings(self) -> None:
        dialog = SecuritySettingsDialog(self._settings, self)
        if dialog.exec() != SecuritySettingsDialog.DialogCode.Accepted:
            return
        self._settings = dialog.result_settings()
        save_settings(self._settings)
        self._clipboard.set_timeout(self._settings.clipboard_timeout_ms)
        self._auto_lock.set_timeout(self._settings.auto_lock_timeout_ms)
        self._auto_lock.set_enabled(self._settings.auto_lock_enabled)
        app = QApplication.instance()
        if isinstance(app, QApplication):
            try:
                mode = ThemeMode(self._settings.theme)
            except ValueError:
                mode = ThemeMode.DARK
            apply_theme(app, mode)
        self.statusBar().showMessage("Settings saved", 3000)
        self._auto_lock.activity()

    def open_plugins(self) -> None:
        dialog = PluginMarketplaceDialog(self._plugins, self)
        dialog.exec()

    def open_installed_plugins(self) -> None:
        dialog = PluginDialog(self._plugins, self)
        dialog.exec()

    def _run_search(self) -> None:
        if self._dbm.active is None:
            return
        query = self._search_box.text().strip()
        filt = self._filter_bar.current_filter(query=query)
        self._active_filter = filt
        if not query and filt.is_empty():
            group_uuid = self._group_tree.selected_group_uuid()
            if group_uuid:
                self._on_group_selected(group_uuid)
            return
        hits = self._search.search(query, entry_filter=filt)
        self._entry_list.set_entries([h.entry for h in hits])
        self.statusBar().showMessage(f"{len(hits)} result(s)", 3000)
        self._auto_lock.activity()

    def _on_filter_changed(self, filt: object) -> None:
        if isinstance(filt, EntryFilter):
            self._active_filter = filt
        self._run_search()

    def _sync_tabs(self) -> None:
        self._updating_tabs = True
        try:
            self._db_tabs.clear()
            active = self._dbm.active_id
            active_index = 0
            for index, session_id in enumerate(self._dbm.session_ids()):
                name = self._dbm.display_name(session_id)
                self._db_tabs.addTab(QWidget(), name)
                self._db_tabs.setTabToolTip(index, session_id)
                if session_id == active:
                    active_index = index
            if self._db_tabs.count():
                self._db_tabs.setCurrentIndex(active_index)
        finally:
            self._updating_tabs = False

    def _refresh_ui(self) -> None:
        self._sync_tabs()
        if self._dbm.active is None:
            self._stack.setCurrentWidget(self._empty)
            self._empty.set_recent(load_recent_databases())
            self._group_tree.clear()
            self._entry_list.set_entries([])
            self._clear_entry_panels()
            self._audit_dash.clear()
            self._groups_dock.hide()
            self._audit_dock.hide()
            self.setWindowTitle(f"KDBXStudio {__version__}")
            return
        self._groups_dock.show()
        self._audit_dock.show()
        self._stack.setCurrentIndex(1)
        name = self._dbm.display_name()
        self.setWindowTitle(f"KDBXStudio — {name}")
        groups = self._dbm.list_groups()
        root = self._dbm.root_group_uuid()
        self._group_tree.set_groups(groups, root)
        self._on_group_selected(root)
        self._refresh_audit()

    def _refresh_audit(self) -> None:
        if self._dbm.active is None:
            self._audit_dash.clear()
            return
        report = self._audit.run()
        self._audit_dash.show_report(report)
        results = self._plugins.context.emit("audit.completed", report=report)
        if results:
            self._plugins.context.set("duplicate_highlight.count", results[-1])
        self._auto_lock.activity()

    def _clear_entry_panels(self) -> None:
        self._current_entry_uuid = None
        self._entry_detail.clear()
        self._history.clear()
        self._attachments.clear()
        self._pem.clear()
        self._totp.clear()

    def _show_entry(self, entry_uuid: str) -> None:
        entry = self._dbm.get_entry(entry_uuid)
        if entry is None:
            self._clear_entry_panels()
            return
        self._current_entry_uuid = entry_uuid
        self._entry_detail.load_entry(entry)
        self._totp.set_otp(entry.otp)
        self._history.set_history(self._dbm.list_history(entry_uuid))
        self._attachments.set_attachments(self._dbm.list_attachments(entry_uuid))
        self._pem.inspect_entry(entry)

    def _add_attachment(self) -> None:
        if not self._ensure_writable():
            return
        if not self._current_entry_uuid or self._dbm.active is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Add Attachment", str(Path.home()), "All Files (*)"
        )
        if not path:
            return
        file_path = Path(path)
        try:
            data = file_path.read_bytes()
            self._dbm.add_attachment(self._current_entry_uuid, file_path.name, data)
            self._show_entry(self._current_entry_uuid)
            self.statusBar().showMessage(f"Attached {file_path.name}", 3000)
        except (OSError, DatabaseError) as exc:
            QMessageBox.critical(self, "Attachment failed", str(exc))
        self._auto_lock.activity()

    def _delete_attachment(self, attachment_id: int) -> None:
        if not self._ensure_writable():
            return
        if not self._current_entry_uuid:
            return
        try:
            self._dbm.delete_attachment(self._current_entry_uuid, attachment_id)
            self._show_entry(self._current_entry_uuid)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Remove failed", str(exc))
        self._auto_lock.activity()

    def _on_tab_changed(self, index: int) -> None:
        if self._updating_tabs or index < 0:
            return
        session_id = self._db_tabs.tabToolTip(index)
        if session_id and session_id != self._dbm.active_id:
            self._dbm.set_active(session_id)
        self._auto_lock.activity()

    def _on_tab_close(self, index: int) -> None:
        session_id = self._db_tabs.tabToolTip(index)
        if session_id:
            self._dbm.close(session_id)

    def _on_group_selected(self, group_uuid: str) -> None:
        if self._dbm.active is None:
            return
        entries = self._dbm.list_entries(group_uuid)
        self._entry_list.set_entries(entries)
        self._auto_lock.activity()

    def _on_entry_selected(self, entry_uuid: str) -> None:
        self._show_entry(entry_uuid)
        self._auto_lock.activity()

    def _on_finding_activated(self, entry_uuid: str) -> None:
        entry = self._dbm.get_entry(entry_uuid)
        if entry:
            self._entry_list.set_entries([entry])
            self._show_entry(entry_uuid)

    def _on_save_entry(self, data: dict) -> None:
        if not self._ensure_writable():
            return
        try:
            entry = self._dbm.update_entry(
                data["uuid"],
                title=data["title"],
                username=data["username"],
                password=data["password"],
                url=data["url"],
                notes=data["notes"],
                otp=self._totp.otp_value(),
                custom_properties=data.get("custom_properties"),
            )
            group_uuid = self._group_tree.selected_group_uuid()
            if group_uuid:
                self._on_group_selected(group_uuid)
            self._show_entry(entry.uuid)
            self.statusBar().showMessage(
                "Entry updated (history saved; save database to persist)", 4000
            )
            self._refresh_audit()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Update failed", str(exc))
        self._auto_lock.activity()

    def _on_copy_password(self, password: str) -> None:
        self._clipboard.copy(password)
        secs = self._settings.clipboard_timeout_ms // 1000
        self.statusBar().showMessage(f"Password copied (clears in {secs}s)", 3000)
        self._auto_lock.activity()

    def _on_auto_lock(self) -> None:
        if not self._dbm.session_ids():
            return
        paths = self._dbm.session_paths()
        if self._settings.clear_clipboard_on_lock:
            self._clipboard.cancel()
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.clear()
        self._dbm.close_all()
        self._clear_entry_panels()
        self.statusBar().showMessage("Databases locked", 5000)
        if paths:
            dialog = UnlockDialog(self, path=paths[0], create_mode=False)
            if dialog.exec() == UnlockDialog.DialogCode.Accepted:
                try:
                    self._dbm.open(
                        dialog.database_path(),
                        password=dialog.password(),
                        keyfile=dialog.keyfile(),
                    )
                except (InvalidCredentialsError, DatabaseError) as exc:
                    QMessageBox.critical(self, "Unlock failed", str(exc))
        self._auto_lock.activity()

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "About KDBXStudio",
            (
                f"<b>KDBXStudio</b> {__version__}<br>"
                "Modern Qt6 KDBX password manager for Linux.<br>"
                "License: <b>GPL-3.0-or-later</b><br><br>"
                "<b>Cuma KURT</b><br>"
                '<a href="mailto:cumakurt@gmail.com">cumakurt@gmail.com</a><br>'
                '<a href="https://www.linkedin.com/in/cuma-kurt-34414917/">'
                "LinkedIn</a> · "
                '<a href="https://github.com/cumakurt/kdbxstudio">GitHub</a>'
            ),
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._dbm.any_dirty():
            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Save active database before quitting?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if answer == QMessageBox.StandardButton.Save and self._dbm.active:
                try:
                    self._dbm.save()
                except DatabaseError as exc:
                    QMessageBox.critical(self, "Save failed", str(exc))
                    event.ignore()
                    return
        self._dbm.close_all()
        self._auto_lock.stop()
        self._persist_layout()
        save_settings(self._settings)
        super().closeEvent(event)

    def save_layout(self) -> None:
        self._persist_layout()
        save_settings(self._settings)
        self.statusBar().showMessage("Layout saved", 3000)

    def reset_layout(self) -> None:
        self.restoreGeometry(self._default_geometry)
        self.restoreState(self._default_state)
        self._settings = self._settings.with_updates(
            window_geometry="",
            window_state="",
        )
        save_settings(self._settings)
        self.statusBar().showMessage("Layout reset", 3000)

    def _persist_layout(self) -> None:
        geometry = b64encode(self.saveGeometry().data()).decode("ascii")
        state = b64encode(self.saveState().data()).decode("ascii")
        self._settings = self._settings.with_updates(
            window_geometry=geometry,
            window_state=state,
        )

    def _restore_layout(self) -> None:
        if self._settings.window_geometry:
            try:
                self.restoreGeometry(
                    QByteArray(b64decode(self._settings.window_geometry))
                )
            except Exception:
                pass
        if self._settings.window_state:
            try:
                self.restoreState(QByteArray(b64decode(self._settings.window_state)))
            except Exception:
                pass

    def _fit_to_screen(self, *, initial: bool = False) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        size = suggested_window_size(screen, scale=detect_ui_scale(screen))
        self.setMinimumSize(900, 560)
        if initial and not self._settings.window_geometry:
            self.resize(size)
            if screen is not None:
                geo = screen.availableGeometry()
                self.move(
                    geo.x() + max(0, (geo.width() - size.width()) // 2),
                    geo.y() + max(0, (geo.height() - size.height()) // 2),
                )

    def _apply_chrome_scale(self) -> None:
        self.setMinimumSize(900, 560)
        if self._main_toolbar is not None:
            self._main_toolbar.setIconSize(QSize(16, 16))
        if hasattr(self, "_groups_dock"):
            self._groups_dock.setMinimumWidth(140)
            self._groups_dock.setMaximumWidth(280)
        if hasattr(self, "_audit_dock"):
            self._audit_dock.setMinimumHeight(80)
            self._audit_dock.setMaximumHeight(180)
        menu = self.menuBar()
        if menu is not None:
            menu.setNativeMenuBar(False)
            font = menu.font()
            font.setPixelSize(11)
            menu.setFont(font)

    def _connect_screen_signals(self) -> None:
        app = QGuiApplication.instance()
        if isinstance(app, QGuiApplication):
            app.primaryScreenChanged.connect(self._on_screen_changed)
        screen = self.screen()
        if screen is not None:
            screen.logicalDotsPerInchChanged.connect(
                lambda _dpi: self._on_screen_changed(screen)
            )
            screen.geometryChanged.connect(lambda _g: self._on_screen_changed(screen))

    def _on_screen_changed(self, screen: object = None) -> None:
        from PySide6.QtGui import QScreen

        target = screen if isinstance(screen, QScreen) else self.screen()
        refresh_theme_for_screen(target)
        self._apply_chrome_scale()
