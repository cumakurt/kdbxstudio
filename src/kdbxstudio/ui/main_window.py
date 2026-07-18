"""Main application window."""

from __future__ import annotations

import re
import shutil
from base64 import b64decode, b64encode
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from threading import Thread

from PySide6.QtCore import QByteArray, QEvent, QPoint, QObject, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QDesktopServices,
    QGuiApplication,
    QIcon,
    QKeySequence,
    QShortcut,
    QShowEvent,
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
    QSystemTrayIcon,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio import __version__
from kdbxstudio.application.audit_engine import AuditEngine, AuditReport
from kdbxstudio.application.database_manager import DatabaseManager
from kdbxstudio.application.favicon import (
    cached_favicon,
    fetch_favicon,
    prefetch_favicons,
)
from kdbxstudio.application.plugin_manager import PluginManager
from kdbxstudio.application.search_engine import EntryFilter, SearchEngine
from kdbxstudio.application.security_dashboard import SecurityDashboardAnalyzer
from kdbxstudio.core.database import (
    DatabaseError,
    EntryView,
    InvalidCredentialsError,
    KdbxDatabase,
)
from kdbxstudio.core.paths import resolve_regular_file
from kdbxstudio.core.totp import current_totp
from kdbxstudio.i18n import get_language, set_language, tr
from kdbxstudio.security.audit_log import log_security_event
from kdbxstudio.security.session import AutoLockController, ClipboardGuard
from kdbxstudio.security.store import (
    clear_recent_databases,
    load_recent_databases,
    load_settings,
    remember_database,
    save_settings,
)
from kdbxstudio.ui.dialogs.command_palette import CommandPalette, PaletteAction
from kdbxstudio.ui.dialogs.health_fix_wizard import HealthFixWizardDialog
from kdbxstudio.ui.dialogs.new_entry_dialog import NewEntryDialog
from kdbxstudio.ui.dialogs.unlock_dialog import UnlockDialog
from kdbxstudio.ui.icons import (
    ICON_ADD,
    ICON_AUDIT,
    ICON_LOCK,
    ICON_OPEN,
    ICON_PALETTE,
    ICON_PLUGIN,
    ICON_SAVE,
    clear_icon_cache,
    icon_tool_button,
    menu_icon,
)
from kdbxstudio.ui.icons.entry_type import clear_entry_icon_cache
from kdbxstudio.ui.icons.group_icons import clear_group_icon_cache
from kdbxstudio.ui.jobs import run_in_thread_pool
from kdbxstudio.ui.screen_lock import ScreenLockWatcher
from kdbxstudio.ui.theme import (
    ACCENT_CHOICES,
    accent_label,
    apply_theme,
    parse_accent,
    refresh_theme_for_screen,
    suggested_window_size,
)
from kdbxstudio.ui.theme.custom_theme import load_custom_theme_json
from kdbxstudio.ui.theme.scale import detect_ui_scale
from kdbxstudio.ui.theme.tokens import THEME_CHOICES, parse_theme, theme_label
from kdbxstudio.ui.widgets.attachment_preview import AttachmentPreviewWidget
from kdbxstudio.ui.widgets.empty_workspace import EmptyWorkspaceWidget
from kdbxstudio.ui.widgets.entry_detail import EntryDetailWidget
from kdbxstudio.ui.widgets.entry_list import EntryListWidget
from kdbxstudio.ui.widgets.filter_bar import FilterBarWidget
from kdbxstudio.ui.widgets.group_tree import GroupTreeWidget
from kdbxstudio.ui.widgets.history_widget import HistoryWidget
from kdbxstudio.ui.widgets.pem_inspector import PemInspectorWidget
from kdbxstudio.ui.widgets.toast import ToastHost
from kdbxstudio.ui.widgets.totp_widget import TotpWidget


class MainWindow(QMainWindow):
    _favicon_ready = Signal()
    _favicon_manual_done = Signal(str, str)  # path_name_or_empty, error_or_empty
    _status_message = Signal(str, int)
    _audit_hibp_done = Signal(object)  # AuditReport
    _autotype_failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"KDBXStudio {__version__}")
        self._apply_window_icon()
        self._main_toolbar: QToolBar | None = None
        self._settings = load_settings()
        set_language(self._settings.language)
        if self._settings.custom_theme_path:
            try:
                load_custom_theme_json(self._settings.custom_theme_path)
            except (OSError, ValueError, TypeError):
                pass

        self._dbm = DatabaseManager()
        self._search = SearchEngine(self._dbm)
        self._audit = AuditEngine(self._dbm)
        self._security_analyzer = SecurityDashboardAnalyzer(self._dbm)
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
        self._tray: QSystemTrayIcon | None = None
        self._quitting = False
        self._startup_done = False
        self._workspace_layout: QVBoxLayout | None = None

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
        # Skip D-Bus screensaver hooks under offscreen/CI to avoid noisy failures.
        import os

        if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen":
            self._screen_lock = None
        else:
            self._screen_lock = ScreenLockWatcher(self._on_auto_lock, parent=self)
        self._vault_busy = False

        self._db_tabs = QTabWidget()
        self._db_tabs.setTabsClosable(True)
        self._db_tabs.setDocumentMode(True)
        self._db_tabs.currentChanged.connect(self._on_tab_changed)
        self._db_tabs.tabCloseRequested.connect(self._on_tab_close)

        self._group_tree = GroupTreeWidget()
        self._entry_list = EntryListWidget()
        self._entry_detail = EntryDetailWidget(clipboard_guard=self._clipboard)
        self._history = HistoryWidget()
        self._attachments = AttachmentPreviewWidget()
        self._attachments.set_data_loader(self._load_attachment_bytes)
        self._pem = PemInspectorWidget()
        self._totp = TotpWidget()
        self._audit_dialog = None
        self._audit_hibp_generation = 0
        self._last_foreign_window_title: str | None = None
        self._window_title_timer = QTimer(self)
        self._window_title_timer.setInterval(750)
        self._window_title_timer.timeout.connect(self._sample_foreign_window_title)
        self._window_title_timer.start()
        self._file_watcher = None
        self._file_watch_ignore: set[str] = set()
        self._browser_bridge = None
        self._favicon_ready.connect(self._on_favicon_fetched)
        self._favicon_manual_done.connect(self._on_favicon_manual_done)
        self._audit_hibp_done.connect(self._on_audit_hibp_done)
        self._autotype_failed.connect(self._on_autotype_failed)
        self._status_message.connect(self._show_status_message)
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText(tr("Search entries…"))
        self._search_box.setAccessibleName(tr("Universal search"))
        self._search_box.setClearButtonEnabled(True)
        self._search_box.returnPressed.connect(self._run_search)
        self._search_box.textChanged.connect(self._on_search_text_changed)
        self._filter_bar = FilterBarWidget()
        self._filter_bar.filter_changed.connect(self._on_filter_changed)

        self._entry_tabs = QTabWidget()
        self._entry_tabs.setObjectName("entryDetailPane")
        self._entry_tabs.addTab(self._entry_detail, tr("Entry"))
        self._entry_tabs.addTab(self._totp, tr("TOTP"))
        self._entry_tabs.addTab(self._history, tr("History"))
        self._entry_tabs.addTab(self._attachments, tr("Attachments"))
        self._entry_tabs.addTab(self._pem, tr("Certificates / SSH"))

        self._db_tabs.setObjectName("dbTabs")
        self._entry_list.setObjectName("entryListPane")
        self._group_tree.setObjectName("groupTreePane")
        self._group_tree.setAlternatingRowColors(True)

        workspace = QWidget()
        workspace.setObjectName("workspaceRoot")
        center_layout = QVBoxLayout(workspace)
        self._workspace_layout = center_layout
        self._workspace_widget = workspace
        self._db_tabs.setMaximumHeight(28)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center_layout.addWidget(self._db_tabs)

        chrome = QWidget()
        chrome.setObjectName("workspaceChrome")
        chrome_layout = QVBoxLayout(chrome)
        chrome_layout.setContentsMargins(12, 8, 12, 8)
        chrome_layout.setSpacing(6)
        chrome_layout.addWidget(self._search_box)
        chrome_layout.addWidget(self._filter_bar)
        center_layout.addWidget(chrome)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("workspaceSplitter")
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(5)
        splitter.addWidget(self._entry_list)
        splitter.addWidget(self._entry_tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([360, 560])
        self._workspace_splitter = splitter
        center_layout.addWidget(splitter, stretch=1)
        self._apply_ui_density()

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
        self._setup_tray()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(tr("Ready"))
        self._toast = ToastHost(self)
        self._locked_tray = False

        self._group_tree.group_selected.connect(self._on_group_selected)
        self._group_tree.entry_drop_requested.connect(self._on_entry_dropped_on_group)
        self._entry_list.entry_selected.connect(self._on_entry_selected)
        self._entry_list.favicon_prefetch_requested.connect(
            self._prefetch_entry_favicons
        )
        self._entry_detail.save_requested.connect(self._on_save_entry)
        self._entry_detail.copy_password_requested.connect(self._on_copy_password)
        self._entry_detail.generate_password_requested.connect(
            self.open_password_generator
        )
        self._history.restore_requested.connect(self._restore_history)
        self._totp.copy_requested.connect(self._on_copy_password)
        self._attachments.add_requested.connect(self._add_attachment)
        self._attachments.delete_requested.connect(self._delete_attachment)
        self._attachments.files_dropped.connect(self._on_files_dropped)
        self._entry_list.delete_requested.connect(lambda: self.delete_entry(False))
        self._entry_list.permanent_delete_requested.connect(
            lambda: self.delete_entry(True)
        )
        self._entry_list.customContextMenuRequested.connect(
            self._on_entry_list_context_menu
        )
        self._group_tree.customContextMenuRequested.connect(
            self._on_group_tree_context_menu
        )
        self._dbm.add_listener(self._refresh_ui)
        self._audit_timer = QTimer(self)
        self._audit_timer.setSingleShot(True)
        self._audit_timer.setInterval(350)
        self._audit_timer.timeout.connect(self._run_debounced_audit)

        from kdbxstudio.application.file_watch import DatabaseFileWatcher

        self._file_watcher = DatabaseFileWatcher(self)
        self._file_watcher.path_changed.connect(self._on_database_file_changed)

        self._bind_shortcuts()
        self._install_idle_filters()
        self._default_geometry = self.saveGeometry()
        self._default_state = self.saveState()
        self._restore_layout()
        self._empty.set_recent(load_recent_databases())
        self._apply_chrome_scale()
        self._connect_screen_signals()
        # Start with docks hidden until a database is open.
        self._groups_dock.hide()
        self._auto_lock.activity()
        self._sync_browser_bridge()
        self._sync_file_watches()

    def _bind_shortcuts(self) -> None:
        for seq in ("Ctrl+K", "Ctrl+Shift+P"):
            shortcut = QShortcut(QKeySequence(seq), self)
            shortcut.activated.connect(self.open_command_palette)

        focus_search = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_search.activated.connect(self._focus_search)

        copy_user = QShortcut(QKeySequence("Ctrl+U"), self)
        copy_user.activated.connect(self._quick_copy_username)

        copy_pass = QShortcut(QKeySequence("Ctrl+B"), self)
        copy_pass.activated.connect(self._quick_copy_password)

        copy_url = QShortcut(QKeySequence("Ctrl+Shift+U"), self)
        copy_url.activated.connect(self._quick_copy_url)

        copy_totp = QShortcut(QKeySequence("Ctrl+T"), self)
        copy_totp.activated.connect(self._quick_copy_totp)

    def _get_selected_entry(self) -> EntryView | None:
        uuid = self._entry_list.selected_entry_uuid() or self._current_entry_uuid
        if not uuid or self._dbm.active is None:
            return None
        return self._dbm.get_entry(uuid)

    def _quick_copy_username(self) -> None:
        entry = self._get_selected_entry()
        if entry is None:
            return
        if entry.username:
            self._clipboard.copy(entry.username)
            self.statusBar().showMessage(tr("Username copied"), 3000)

    def _quick_copy_password(self) -> None:
        entry = self._get_selected_entry()
        if entry is None:
            return
        if entry.password:
            self._clipboard.copy(entry.password)
            secs = self._settings.clipboard_timeout_ms // 1000
            self.statusBar().showMessage(
                tr("Password copied (clears in {secs}s)").format(secs=secs),
                3000,
            )

    def _quick_copy_url(self) -> None:
        entry = self._get_selected_entry()
        if entry is None:
            return
        if entry.url:
            self._clipboard.copy(entry.url)
            self.statusBar().showMessage(tr("URL copied"), 3000)

    def _quick_copy_totp(self) -> None:
        entry = self._get_selected_entry()
        if entry is None or not entry.otp:
            return
        status = current_totp(entry.otp)
        if status.valid and status.code:
            self._clipboard.copy(status.code)
            self.statusBar().showMessage(tr("TOTP code copied"), 3000)

    def _on_entry_list_context_menu(self, pos: QPoint) -> None:
        self._entry_list.select_row_at(pos)
        has_selection = bool(self._entry_list.selected_entry_uuids())
        entry = self._get_selected_entry() if has_selection else None
        multi = len(self._entry_list.selected_entry_uuids()) > 1

        menu = QMenu(self)
        menu.addAction(
            menu_icon("person_add"), tr("Add Entry…"), self.add_entry
        )
        menu.addAction(
            menu_icon("article"),
            tr("New from Template…"),
            self.add_entry_from_template,
        )
        menu.addSeparator()

        copy_user = menu.addAction(
            menu_icon("content_copy"),
            tr("Copy Username"),
            self._quick_copy_username,
        )
        copy_pass = menu.addAction(
            menu_icon("content_copy"),
            tr("Copy Password"),
            self._quick_copy_password,
        )
        copy_url = menu.addAction(
            menu_icon("content_copy"), tr("Copy URL"), self._quick_copy_url
        )
        copy_totp = menu.addAction(
            menu_icon("content_copy"), tr("Copy TOTP"), self._quick_copy_totp
        )
        for action in (copy_user, copy_pass, copy_url, copy_totp):
            action.setEnabled(bool(entry) and not multi)
        if entry is not None and not multi:
            copy_user.setEnabled(bool(entry.username))
            copy_pass.setEnabled(bool(entry.password))
            copy_url.setEnabled(bool(entry.url))
            copy_totp.setEnabled(bool(entry.otp))

        menu.addSeparator()
        autotype = menu.addAction(
            menu_icon("auto_fix_fill"), tr("Auto-Type"), self.auto_type_selected
        )
        move = menu.addAction(
            menu_icon("drive_file_move"),
            tr("Move to Group…"),
            self.move_selected_entry,
        )
        favicon = menu.addAction(
            menu_icon("image"), tr("Fetch Favicon"), self.fetch_selected_favicon
        )
        for action in (autotype, move, favicon):
            action.setEnabled(has_selection)
        if multi:
            autotype.setEnabled(False)
            favicon.setEnabled(False)

        menu.addSeparator()
        recycle = menu.addAction(
            menu_icon("delete"),
            tr("Move to Recycle Bin"),
            lambda: self.delete_entry(False),
        )
        purge = menu.addAction(
            menu_icon("delete"),
            tr("Delete Permanently"),
            lambda: self.delete_entry(True),
        )
        recycle.setEnabled(has_selection)
        purge.setEnabled(has_selection)
        menu.exec(self._entry_list.mapToGlobal(pos))

    def _on_group_tree_context_menu(self, pos: QPoint) -> None:
        self._group_tree.select_at(pos)
        group_uuid = self._group_tree.selected_group_uuid()
        is_bin = False
        if group_uuid and self._dbm.active is not None:
            for group in self._dbm.list_groups():
                if group.uuid == group_uuid:
                    is_bin = group.is_recycle_bin
                    break

        menu = QMenu(self)
        add_group = menu.addAction(
            menu_icon("folder"), tr("Add Group…"), self.add_group
        )
        add_entry = menu.addAction(
            menu_icon("person_add"), tr("Add Entry…"), self.add_entry
        )
        add_template = menu.addAction(
            menu_icon("article"),
            tr("New from Template…"),
            self.add_entry_from_template,
        )
        menu.addSeparator()
        rename = menu.addAction(
            menu_icon("edit"), tr("Rename Group…"), self.rename_group
        )
        delete = menu.addAction(
            menu_icon("delete"),
            tr("Move Group to Recycle Bin"),
            self.delete_group,
        )
        menu.addSeparator()
        empty_bin = menu.addAction(
            menu_icon("delete_sweep"),
            tr("Empty Recycle Bin…"),
            self.empty_recycle_bin,
        )

        has_group = group_uuid is not None
        add_group.setEnabled(has_group and not is_bin)
        add_entry.setEnabled(has_group and not is_bin)
        add_template.setEnabled(has_group and not is_bin)
        rename.setEnabled(has_group and not is_bin)
        delete.setEnabled(has_group and not is_bin)
        empty_bin.setEnabled(self._dbm.active is not None)
        menu.exec(self._group_tree.mapToGlobal(pos))

    def _install_idle_filters(self) -> None:
        self.installEventFilter(self)
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        etype = event.type()
        if etype in (
            QEvent.Type.KeyPress,
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseButtonDblClick,
            QEvent.Type.Wheel,
        ):
            self._auto_lock.activity()
        return super().eventFilter(watched, event)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        if self._startup_done:
            return
        self._startup_done = True
        self._run_startup_tasks()

    def _show_status_message(self, message: str, timeout_ms: int) -> None:
        self.statusBar().showMessage(message, timeout_ms)
        if hasattr(self, "_toast") and self._toast is not None:
            self._toast.show_message(message, timeout_ms)

    def _run_startup_tasks(self) -> None:
        if self._settings.check_updates_on_start:
            Thread(target=self._check_updates_background, daemon=True).start()
        if self._settings.start_minimized_to_tray and self._tray is not None:
            QTimer.singleShot(0, self.hide)

    def _check_updates_background(self) -> None:
        from kdbxstudio.application.update_check import check_github_release

        try:
            info = check_github_release(__version__)
        except Exception:
            return
        # Startup: only notify when an update is available (avoid noise).
        if info.newer:
            self._status_message.emit(
                tr("Update available: {latest} (you have {current})").format(
                    latest=info.latest,
                    current=info.current,
                ),
                10000,
            )

    def check_for_updates(self, *, interactive: bool = True) -> None:
        from kdbxstudio.application.update_check import check_github_release

        try:
            info = check_github_release(__version__)
        except Exception as exc:
            if interactive:
                QMessageBox.warning(self, tr("Update check"), str(exc))
            return

        source_labels = {
            "release": tr("GitHub Release"),
            "tag": tr("GitHub Tag"),
            "repository": tr("GitHub repository"),
        }
        source = source_labels.get(info.source, info.source)
        detail = tr(
            "Installed version: {current}\n"
            "GitHub version: {latest}\n"
            "Source: {source}"
        ).format(current=info.current, latest=info.latest, source=source)

        if info.newer:
            if interactive:
                answer = QMessageBox.information(
                    self,
                    tr("Update available"),
                    tr(
                        "A newer version is available on GitHub.\n\n"
                        "{detail}\n\nOpen the release page?"
                    ).format(detail=detail),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if answer == QMessageBox.StandardButton.Yes:
                    QDesktopServices.openUrl(QUrl(info.html_url))
            else:
                self.statusBar().showMessage(
                    tr("Update available: {latest} (you have {current})").format(
                        latest=info.latest,
                        current=info.current,
                    ),
                    10000,
                )
        elif info.equal:
            if interactive:
                QMessageBox.information(
                    self,
                    tr("Up to date"),
                    tr(
                        "KDBXStudio is up to date.\n\n{detail}"
                    ).format(detail=detail),
                )
            else:
                self.statusBar().showMessage(
                    tr("KDBXStudio {version} is up to date").format(
                        version=info.current
                    ),
                    4000,
                )
        else:
            # Local build is ahead of published GitHub version.
            if interactive:
                QMessageBox.information(
                    self,
                    tr("Up to date"),
                    tr(
                        "Your installed version is newer than the version on GitHub.\n\n"
                        "{detail}"
                    ).format(detail=detail),
                )
            else:
                self.statusBar().showMessage(
                    tr("KDBXStudio {version} is up to date").format(
                        version=info.current
                    ),
                    4000,
                )
        self._auto_lock.activity()

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        menu = QMenu(self)
        show_action = QAction(menu_icon("folder_open"), tr("Show"), self)
        show_action.triggered.connect(self._tray_show)
        menu.addAction(show_action)
        lock_action = QAction(menu_icon("lock"), tr("Lock"), self)
        lock_action.triggered.connect(self._on_auto_lock)
        menu.addAction(lock_action)
        menu.addSeparator()
        quit_action = QAction(menu_icon("close"), tr("Quit"), self)
        quit_action.triggered.connect(self._tray_quit)
        menu.addAction(quit_action)

        if self._tray is not None:
            self._tray.setToolTip(f"KDBXStudio {__version__}")
            self._tray.setContextMenu(menu)
            return

        tray = QSystemTrayIcon(self)
        icon = self.windowIcon()
        if icon.isNull():
            icon = QIcon.fromTheme("dialog-password")
        tray.setIcon(icon)
        tray.setToolTip(f"KDBXStudio {__version__}")
        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        self._tray = tray
        self._tray_normal_icon = icon
        self._tray_lock_icon = menu_icon("lock", size=22)

    def _set_tray_locked(self, locked: bool) -> None:
        if self._tray is None:
            return
        self._locked_tray = locked
        if locked:
            lock_icon = getattr(self, "_tray_lock_icon", None)
            if lock_icon is not None:
                self._tray.setIcon(lock_icon)
            self._tray.setToolTip(tr("KDBXStudio — locked"))
        else:
            normal = getattr(self, "_tray_normal_icon", None)
            if normal is not None:
                self._tray.setIcon(normal)
            self._tray.setToolTip(f"KDBXStudio {__version__}")

    def _retranslate_shell(self) -> None:
        """Rebuild menus/toolbar/tray after a language change."""
        self.menuBar().clear()
        self._build_menus()
        if self._main_toolbar is not None:
            self.removeToolBar(self._main_toolbar)
            self._main_toolbar.deleteLater()
            self._main_toolbar = None
        self._build_toolbar()
        self._setup_tray()
        if hasattr(self, "_groups_dock"):
            self._groups_dock.setWindowTitle(tr("Groups"))
        self._search_box.setPlaceholderText(tr("Search entries…"))
        self._search_box.setAccessibleName(tr("Universal search"))
        for index, key in enumerate(
            ("Entry", "TOTP", "History", "Attachments", "Certificates / SSH")
        ):
            self._entry_tabs.setTabText(index, tr(key))
        self._group_tree.setHeaderLabel(tr("Groups"))
        self._entry_list.setHorizontalHeaderLabels(
            [tr(col) for col in self._entry_list.COLUMNS]
        )

    def _tray_show(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._auto_lock.activity()

    def _tray_quit(self) -> None:
        self._quitting = True
        self.close()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self._tray_show()

    def _apply_ui_density(self) -> None:
        if self._workspace_layout is None:
            return
        self._workspace_layout.setContentsMargins(0, 0, 0, 0)
        self._workspace_layout.setSpacing(0)
        chrome = self._workspace_widget.findChild(QWidget, "workspaceChrome")
        if chrome is None or chrome.layout() is None:
            return
        if self._settings.ui_density == "comfortable":
            chrome.layout().setContentsMargins(16, 10, 16, 10)
            chrome.layout().setSpacing(8)
        else:
            chrome.layout().setContentsMargins(12, 8, 12, 8)
            chrome.layout().setSpacing(6)

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
        self._plugins.activate_all()

    def _setup_docks(self) -> None:
        groups_dock = QDockWidget(tr("GROUPS"), self)
        groups_dock.setObjectName("groupsDock")
        groups_dock.setWidget(self._group_tree)
        groups_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        groups_dock.setMinimumWidth(160)
        groups_dock.setMaximumWidth(280)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, groups_dock)

        self._groups_dock = groups_dock
        self.resizeDocks([groups_dock], [180], Qt.Orientation.Horizontal)

    def _build_menus(self) -> None:
        def act(
            text: str,
            slot: object,
            *,
            shortcut: QKeySequence | str | None = None,
            icon_name: str | None = None,
        ) -> QAction:
            action = QAction(text, self)
            if icon_name:
                action.setIcon(menu_icon(icon_name))
            if shortcut is not None:
                if isinstance(shortcut, str):
                    action.setShortcut(QKeySequence(shortcut))
                else:
                    action.setShortcut(shortcut)
            action.triggered.connect(slot)
            return action

        file_menu = self.menuBar().addMenu(tr("&File"))
        file_menu.addAction(
            act(tr("Open…"), self.open_database, shortcut=QKeySequence.StandardKey.Open, icon_name="folder_open")
        )
        file_menu.addAction(
            act(tr("New Database…"), self.create_database, shortcut=QKeySequence.StandardKey.New, icon_name="note_add")
        )
        file_menu.addAction(
            act(tr("Save"), self.save_database, shortcut=QKeySequence.StandardKey.Save, icon_name="save")
        )
        file_menu.addAction(act(tr("Export CSV…"), self.export_csv, icon_name="upload"))
        file_menu.addAction(act(tr("Import CSV…"), self.import_csv, icon_name="download"))
        file_menu.addAction(act(tr("Database Properties…"), self.show_database_properties, icon_name="info"))
        file_menu.addAction(act(tr("Change Master Password…"), self.change_master_password, icon_name="key"))
        file_menu.addAction(act(tr("Close"), self.close_database, icon_name="close"))

        self._recent_menu = file_menu.addMenu(tr("Open Recent"))
        self._recent_menu.setIcon(menu_icon("history"))
        self._rebuild_recent_menu()

        file_menu.addSeparator()
        file_menu.addAction(
            act(tr("Quit"), self._tray_quit, shortcut=QKeySequence.StandardKey.Quit, icon_name="logout")
        )

        entry_menu = self.menuBar().addMenu(tr("&Entry"))
        entry_menu.addAction(act(tr("Add Entry…"), self.add_entry, icon_name="person_add"))
        entry_menu.addAction(act(tr("New from Template…"), self.add_entry_from_template, icon_name="article"))
        delete_action = act(
            tr("Move to Recycle Bin"),
            lambda: self.delete_entry(False),
            shortcut=QKeySequence(Qt.Key.Key_Delete),
            icon_name="delete",
        )
        entry_menu.addAction(delete_action)
        purge_action = act(
            tr("Delete Permanently"),
            lambda: self.delete_entry(True),
            shortcut="Shift+Delete",
            icon_name="delete_sweep",
        )
        entry_menu.addAction(purge_action)
        entry_menu.addSeparator()
        autotype_action = act(tr("Auto-Type"), self.auto_type_selected, icon_name="auto_fix_fill")
        autotype_action.setShortcuts(
            [QKeySequence("Ctrl+Shift+V"), QKeySequence("Ctrl+Alt+A")]
        )
        entry_menu.addAction(autotype_action)
        entry_menu.addAction(act(tr("Move to Group…"), self.move_selected_entry, icon_name="drive_file_move"))
        entry_menu.addAction(act(tr("Fetch Favicon"), self.fetch_selected_favicon, icon_name="image"))

        group_menu = self.menuBar().addMenu(tr("&Group"))
        group_menu.addAction(act(tr("Add Group…"), self.add_group, icon_name="folder"))
        rename_group = act(tr("Rename Group"), self.rename_group, shortcut=QKeySequence(Qt.Key.Key_F2), icon_name="edit")
        group_menu.addAction(rename_group)
        group_menu.addAction(act(tr("Move Group to Recycle Bin"), self.delete_group, icon_name="delete"))

        tools_menu = self.menuBar().addMenu(tr("&Tools"))
        tools_menu.addAction(act(tr("Security Dashboard…"), self.open_security_dashboard, icon_name="dashboard"))
        tools_menu.addAction(act(tr("Empty Recycle Bin…"), self.empty_recycle_bin, icon_name="delete_sweep"))

        plugins_menu = tools_menu.addMenu(tr("Plugin Center"))
        plugins_menu.setIcon(menu_icon("extension"))
        plugins_menu.addAction(act(tr("Marketplace…"), self.open_plugins, icon_name="extension"))
        plugins_menu.addAction(act(tr("Installed Plugins…"), self.open_installed_plugins, icon_name="extension"))

        tools_menu.addAction(act(tr("Password Generator…"), self.open_password_generator, icon_name="password"))
        tools_menu.addSeparator()
        tools_menu.addAction(act(tr("Merge Database…"), self.merge_database, icon_name="merge"))
        tools_menu.addAction(act(tr("Emergency Sheet…"), self.export_emergency_sheet, icon_name="description"))
        tools_menu.addAction(act(tr("Check for Updates…"), self.check_for_updates, icon_name="system_update"))
        tools_menu.addAction(act(tr("Add Selected PEM to SSH Agent"), self.add_selected_pem_to_agent, icon_name="vpn_key"))
        tools_menu.addSeparator()
        tools_menu.addAction(
            act(tr("Lock All Databases"), self._on_auto_lock, shortcut="Ctrl+L", icon_name="lock")
        )
        tools_menu.addAction(act(tr("Settings…"), self.open_security_settings, icon_name="settings"))

        view_menu = self.menuBar().addMenu(tr("&View"))
        view_menu.addAction(self._groups_dock.toggleViewAction())
        view_menu.addSeparator()
        view_menu.addAction(act(tr("Save Layout"), self.save_layout, icon_name="save"))
        view_menu.addAction(act(tr("Reset Layout"), self.reset_layout, icon_name="refresh"))
        view_menu.addSeparator()
        theme_menu = view_menu.addMenu(tr("Theme"))
        theme_menu.setIcon(menu_icon("contrast"))
        for mode in THEME_CHOICES:
            action = act(
                tr(theme_label(mode)),
                lambda checked=False, v=mode.value: self.set_theme(v),
                icon_name="contrast",
            )
            theme_menu.addAction(action)
        accent_menu = view_menu.addMenu(tr("Accent"))
        accent_menu.setIcon(menu_icon("palette"))
        for accent in ACCENT_CHOICES:
            action = act(
                tr(accent_label(accent)),
                lambda *_args, a=accent.value: self.set_accent(a),
                icon_name="palette",
            )
            accent_menu.addAction(action)
        view_menu.addAction(
            act(tr("Command Palette…"), self.open_command_palette, shortcut="Ctrl+K", icon_name="terminal")
        )

        help_menu = self.menuBar().addMenu(tr("&Help"))
        help_menu.addAction(act(tr("About"), self._about, icon_name="info"))

    def _build_toolbar(self) -> None:
        toolbar = QToolBar(tr("Main"))
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)
        self._main_toolbar = toolbar

        def add_icon(name: str, tip: str, slot: object) -> None:
            button = icon_tool_button(name, tip, toolbar, size=18)
            button.clicked.connect(slot)
            toolbar.addWidget(button)

        add_icon(ICON_OPEN, tr("Open database"), self.open_database)
        add_icon(ICON_SAVE, tr("Save database"), self.save_database)
        toolbar.addSeparator()
        add_icon(ICON_ADD, tr("Add entry"), self.add_entry)
        toolbar.addSeparator()
        add_icon(ICON_PALETTE, tr("Command palette"), self.open_command_palette)
        add_icon(ICON_AUDIT, tr("Security Dashboard"), self.open_security_dashboard)
        add_icon(ICON_PLUGIN, tr("Plugin marketplace"), self.open_plugins)
        toolbar.addSeparator()
        add_icon(ICON_LOCK, tr("Lock all databases"), self._on_auto_lock)

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
            empty = QAction(tr("No recent databases"), self)
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
        clear_action = QAction(tr("Clear Recent"), self)
        clear_action.triggered.connect(self._clear_recent)
        self._recent_menu.addAction(clear_action)

    def _open_recent(self, path: Path) -> None:
        if not path.is_file():
            QMessageBox.warning(
                self,
                tr("Missing file"),
                tr("Database no longer exists:\n{path}").format(path=path),
            )
            self._rebuild_recent_menu()
            return
        dialog = UnlockDialog(self, path=path, create_mode=False)
        if dialog.exec() != UnlockDialog.DialogCode.Accepted:
            return
        self._start_vault_open(dialog, create=False)

    def _consume_unlock_dialog(
        self, dialog: UnlockDialog
    ) -> tuple[Path, str | None, Path | None]:
        path = dialog.database_path()
        password = dialog.password()
        keyfile = dialog.keyfile()
        dialog.clear_secrets()
        return path, password, keyfile

    def _start_vault_open(self, dialog: UnlockDialog, *, create: bool) -> None:
        if self._vault_busy:
            return
        path, password, keyfile = self._consume_unlock_dialog(dialog)
        self._vault_busy = True
        self.setEnabled(False)
        self.statusBar().showMessage(
            tr("Creating database…") if create else tr("Unlocking…"), 0
        )

        def work() -> tuple[KdbxDatabase, Path]:
            db = KdbxDatabase()
            if create:
                db.create(path, password=password, keyfile=keyfile)
            else:
                db.open(path, password=password, keyfile=keyfile)
            return db, path

        def on_ok(result: object) -> None:
            self._vault_busy = False
            self.setEnabled(True)
            db, opened = result  # type: ignore[misc]
            assert isinstance(db, KdbxDatabase)
            assert isinstance(opened, Path)
            self._dbm.adopt(db, opened)
            remember_database(opened)
            self._rebuild_recent_menu()
            verb = tr("Created") if create else tr("Opened")
            self.statusBar().showMessage(f"{verb} {opened.name}", 5000)
            log_security_event(
                "vault_created" if create else "vault_unlocked",
                database=opened.name,
            )
            self._auto_lock.activity()

        def on_err(message: str) -> None:
            self._vault_busy = False
            self.setEnabled(True)
            lower = message.lower()
            if "invalid password" in lower or "credentials" in lower:
                QMessageBox.critical(
                    self, tr("Unlock failed"), tr("Invalid password or key file.")
                )
                log_security_event("vault_unlock_failed", database=path.name)
            else:
                title = tr("Create failed") if create else tr("Open failed")
                QMessageBox.critical(self, title, message)
                log_security_event(
                    "vault_create_failed" if create else "vault_open_failed",
                    database=path.name,
                )
            self._auto_lock.activity()

        run_in_thread_pool(work, on_success=on_ok, on_error=on_err, parent=self)

    def _clear_recent(self) -> None:
        clear_recent_databases()
        self._rebuild_recent_menu()
        self._empty.set_recent([])

    def import_csv(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, tr("Import"), tr("Open a database first."))
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Import CSV"),
            str(Path.home()),
            tr("CSV Files (*.csv)"),
        )
        if not path:
            return
        try:
            result = self._dbm.import_csv(path)
            message = (
                f"Imported {result.created} entries "
                f"({result.skipped} skipped, "
                f"{result.groups_created} groups created)"
            )
            if result.skipped and result.created == 0:
                message += (
                    ". Tip: Bitwarden/Chrome/KeePass CSV need columns like "
                    "name/title, username/login, password, url/uri, notes/folder"
                )
            elif result.skipped:
                message += (
                    ". Some rows skipped — check Bitwarden/Chrome/KeePass column names"
                )
            self.statusBar().showMessage(message, 8000)
        except (OSError, DatabaseError, KeyError) as exc:
            QMessageBox.critical(
                self,
                tr("Import failed"),
                f"{exc}\n\nExpected columns (Bitwarden/Chrome/KeePass CSV):\n"
                "name or title, username or login_username, password,\n"
                "url / login_uri / uri, notes, folder / group",
            )
        self._auto_lock.activity()

    def change_master_password(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, tr("Credentials"), tr("Open a database first."))
            return
        from kdbxstudio.ui.dialogs.change_credentials_dialog import (
            ChangeCredentialsDialog,
        )

        dialog = ChangeCredentialsDialog(self)
        if dialog.exec() != ChangeCredentialsDialog.DialogCode.Accepted:
            return
        password = dialog.password()
        keyfile = dialog.keyfile()
        clear_keyfile = dialog.clear_keyfile()
        dialog.clear_secrets()
        try:
            self._dbm.change_credentials(
                password=password,
                keyfile=keyfile,
                clear_keyfile=clear_keyfile,
            )
            self._save_with_backup()
            self.statusBar().showMessage(
                "Master credentials updated and database saved", 5000
            )
            log_security_event("master_credentials_changed")
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Credential change failed"), str(exc))
        self._auto_lock.activity()

    def add_group(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, tr("Add group"), tr("Open a database first."))
            return
        parent = (
            self._group_tree.selected_group_uuid() or self._dbm.root_group_uuid()
        )
        name, ok = QInputDialog.getText(self, tr("New Group"), tr("Group name:"))
        if not ok or not name.strip():
            return
        try:
            group = self._dbm.add_group(parent, name.strip())
            self.statusBar().showMessage(f"Added group '{group.name}'", 3000)
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Add group failed"), str(exc))
        self._auto_lock.activity()

    def rename_group(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            return
        group_uuid = self._group_tree.selected_group_uuid()
        if not group_uuid:
            return
        name, ok = QInputDialog.getText(self, tr("Rename Group"), tr("New name:"))
        if not ok or not name.strip():
            return
        try:
            group = self._dbm.rename_group(group_uuid, name.strip())
            self.statusBar().showMessage(f"Renamed group to '{group.name}'", 3000)
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Rename failed"), str(exc))
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
            tr("Recycle Bin"),
            tr("Move the selected group to the Recycle Bin?"),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self._dbm.delete_group(group_uuid)
            self.statusBar().showMessage(tr("Group moved to Recycle Bin"), 3000)
            self._select_recycle_bin()
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Delete group failed"), str(exc))
        self._auto_lock.activity()

    def export_csv(self) -> None:
        if self._dbm.active is None:
            QMessageBox.information(self, tr("Export"), tr("Open a database first."))
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("Export CSV"),
            str(Path.home() / "kdbxstudio-export.csv"),
            tr("CSV Files (*.csv)"),
        )
        if not path:
            return
        confirm = QMessageBox.warning(
            self,
            tr("Export includes secrets"),
            tr(
                "The CSV file will contain passwords and OTP secrets "
                "in plain text. Continue?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            from kdbxstudio.application.export import export_entries_csv

            entries = self._dbm.all_entries(include_recycle_bin=False)
            export_entries_csv(path, entries)
            self.statusBar().showMessage(f"Exported {len(entries)} entries", 5000)
        except OSError as exc:
            QMessageBox.critical(self, tr("Export failed"), str(exc))
        self._auto_lock.activity()

    def show_database_properties(self) -> None:
        if self._dbm.active is None:
            QMessageBox.information(self, tr("Properties"), tr("Open a database first."))
            return
        from kdbxstudio.ui.dialogs.database_properties_dialog import (
            DatabasePropertiesDialog,
        )

        dialog = DatabasePropertiesDialog(self._dbm.database_info(), self)
        dialog.exec()

    def _restore_history(self, history_index: int) -> None:
        if not self._ensure_writable():
            return
        if not self._current_entry_uuid:
            return
        confirm = QMessageBox.question(
            self,
            tr("Restore revision"),
            tr(
                "Restore this historical revision? "
                "Current values are saved to history first."
            ),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            entry = self._dbm.restore_history(self._current_entry_uuid, history_index)
            self._show_entry(entry.uuid)
            self.statusBar().showMessage(
                tr("Revision restored (save database to persist)"), 4000
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Restore failed"), str(exc))
        self._auto_lock.activity()

    def open_password_generator(self) -> None:
        from kdbxstudio.ui.dialogs.password_generator_dialog import (
            PasswordGeneratorDialog,
        )

        dialog = PasswordGeneratorDialog(self, clipboard_guard=self._clipboard)
        if dialog.exec() != PasswordGeneratorDialog.DialogCode.Accepted:
            return
        password = dialog.password()
        if self._current_entry_uuid:
            self._entry_detail.set_password(password)
            self.statusBar().showMessage(
                tr("Generated password applied to entry (save to keep)"), 4000
            )
        else:
            self._clipboard.copy(password)
            self.statusBar().showMessage(
                tr("Generated password copied to clipboard"), 4000
            )
        self._auto_lock.activity()

    def set_theme(self, theme: str) -> None:
        mode = parse_theme(theme)
        self._settings = self._settings.with_updates(theme=mode.value)
        save_settings(self._settings)
        self._apply_appearance()
        self.statusBar().showMessage(
            tr("Theme: {name}").format(name=tr(theme_label(mode))), 2000
        )

    def set_accent(self, accent: str) -> None:
        aid = parse_accent(accent)
        self._settings = self._settings.with_updates(accent=aid.value)
        save_settings(self._settings)
        self._apply_appearance()
        self.statusBar().showMessage(
            tr("Accent: {name}").format(name=tr(accent_label(aid))), 2000
        )

    def _preview_accent(self, accent: str) -> None:
        """Live-preview accent from Settings without persisting until Save."""
        self._apply_appearance(accent_override=parse_accent(accent))

    def _apply_appearance(self, *, accent_override: object | None = None) -> None:
        """Re-apply theme/accent/scale/font/menu and refresh chrome icons."""
        clear_icon_cache()
        clear_group_icon_cache()
        clear_entry_icon_cache()
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(
                app,
                parse_theme(self._settings.theme),
                accent=accent_override
                if accent_override is not None
                else self._settings.accent,
                ui_density=self._settings.ui_density,
                ui_scale_percent=self._settings.ui_scale_percent,
                font_size=self._settings.font_size,
                menu_size=self._settings.menu_size,
                force=True,
            )
        self._rebuild_toolbar_icons()
        self._apply_chrome_scale()
        # Rebuild group icons after cache clear (fixed palette; ensures fresh pixmaps).
        if self._dbm.active is not None:
            selected = self._group_tree.selected_group_uuid()
            groups = self._dbm.list_groups()
            root = self._dbm.root_group_uuid()
            self._group_tree.set_groups(groups, root, select_uuid=selected or root)
            self._entry_list.refresh_icons()

    def _rebuild_toolbar_icons(self) -> None:
        """Recreate toolbar buttons so outlined icons pick up the new brand tint."""
        if self._main_toolbar is None:
            return
        self.removeToolBar(self._main_toolbar)
        self._main_toolbar.deleteLater()
        self._main_toolbar = None
        self._build_toolbar()

    def open_command_palette(self) -> None:
        actions = [
            PaletteAction(
                "open",
                tr("Open Database…"),
                ("file", "open"),
                self.open_database,
                icon="folder_open",
            ),
            PaletteAction(
                "new",
                tr("New Database…"),
                ("create", "new"),
                self.create_database,
                icon="add",
            ),
            PaletteAction(
                "save",
                tr("Save"),
                ("save",),
                self.save_database,
                icon="save",
            ),
            PaletteAction(
                "lock",
                tr("Lock All"),
                ("lock", "security"),
                self._on_auto_lock,
                icon="lock",
            ),
            PaletteAction(
                "add-entry",
                tr("Add Entry…"),
                ("entry", "add"),
                self.add_entry,
                icon="person_add",
            ),
            PaletteAction(
                "template",
                tr("New from Template…"),
                ("template",),
                self.add_entry_from_template,
                icon="article",
            ),
            PaletteAction(
                "generate",
                tr("Password Generator…"),
                ("password", "generate"),
                self.open_password_generator,
                icon="password",
            ),
            PaletteAction(
                "audit",
                tr("Security Dashboard…"),
                ("audit", "health", "findings", "security", "dashboard", "reports"),
                self.open_security_dashboard,
                icon="dashboard",
            ),
            PaletteAction(
                "import",
                tr("Import CSV…"),
                ("import", "csv"),
                self.import_csv,
                icon="download",
            ),
            PaletteAction(
                "export",
                tr("Export CSV…"),
                ("export", "csv"),
                self.export_csv,
                icon="upload",
            ),
            PaletteAction(
                "autotype",
                tr("Auto-Type Selected Entry"),
                ("autotype", "type"),
                self.auto_type_selected,
                icon="auto_fix_fill",
            ),
            PaletteAction(
                "merge",
                tr("Merge Database…"),
                ("merge", "import"),
                self.merge_database,
                icon="merge",
            ),
            PaletteAction(
                "emergency",
                tr("Emergency Sheet…"),
                ("emergency", "print", "sheet"),
                self.export_emergency_sheet,
                icon="description",
            ),
            PaletteAction(
                "updates",
                tr("Check for Updates…"),
                ("update", "version"),
                self.check_for_updates,
                icon="system_update",
            ),
            PaletteAction(
                "move-entry",
                tr("Move Entry to Group…"),
                ("move", "group"),
                self.move_selected_entry,
                icon="drive_file_move",
            ),
            PaletteAction(
                "favicon",
                tr("Fetch Favicon"),
                ("favicon", "icon"),
                self.fetch_selected_favicon,
                icon="image",
            ),
            PaletteAction(
                "plugins",
                tr("Plugin Marketplace…"),
                ("plugin", "market"),
                self.open_plugins,
                icon="extension",
            ),
            PaletteAction(
                "settings",
                tr("Security & Appearance…"),
                ("settings", "theme"),
                self.open_security_settings,
                icon="settings",
            ),
            *[
                PaletteAction(
                    f"theme-{mode.value}",
                    tr("Theme: {name}").format(name=tr(theme_label(mode))),
                    ("theme", mode.value),
                    lambda m=mode: self.set_theme(m.value),
                    icon="contrast",
                )
                for mode in THEME_CHOICES
            ],
            *[
                PaletteAction(
                    f"accent-{accent.value}",
                    tr("Accent: {name}").format(name=tr(accent_label(accent))),
                    ("accent", "color", "palette", accent.value),
                    lambda a=accent: self.set_accent(a.value),
                    icon="palette",
                )
                for accent in ACCENT_CHOICES
            ],
            PaletteAction(
                "focus-search",
                tr("Focus Search"),
                ("search", "find"),
                lambda: self._search_box.setFocus(),
                icon="search",
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
                    icon="history",
                )
            )
        if self._dbm.active is not None:
            for entry in self._dbm.all_entries(include_recycle_bin=False)[:25]:
                title = entry.title or tr("(untitled)")

                def _jump(uuid: str = entry.uuid) -> None:
                    self._show_entry(uuid)

                actions.append(
                    PaletteAction(
                        f"entry:{entry.uuid}",
                        title,
                        (
                            "entry",
                            title.lower(),
                            (entry.username or "").lower(),
                            (entry.url or "").lower(),
                        ),
                        _jump,
                        section="Entries",
                        icon="person",
                    )
                )
        dialog = CommandPalette(actions, self)
        dialog.exec()
        self._auto_lock.activity()

    def open_database(self) -> None:
        dialog = UnlockDialog(self, create_mode=False)
        if dialog.exec() != UnlockDialog.DialogCode.Accepted:
            return
        self._start_vault_open(dialog, create=False)

    def create_database(self) -> None:
        dialog = UnlockDialog(self, create_mode=True)
        if dialog.exec() != UnlockDialog.DialogCode.Accepted:
            return
        self._start_vault_open(dialog, create=True)

    def _ensure_writable(self) -> bool:
        if self._settings.read_only:
            QMessageBox.information(
                self,
                tr("Read-only mode"),
                tr("This session is read-only. Disable it in Security & Appearance."),
            )
            return False
        return True

    def save_database(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, tr("Save"), tr("No database is open."))
            return
        try:
            self._save_with_backup()
            self.statusBar().showMessage(tr("Database saved"), 3000)
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Save failed"), str(exc))
        self._auto_lock.activity()

    def _backup_session(self, session_id: str) -> None:
        """Copy the on-disk vault before overwrite. Best-effort; never blocks save."""
        path = Path(session_id)
        if not path.is_file():
            return
        backup_dir = path.parent / ".kdbxstudio-backups"
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{path.stem}_{timestamp}{path.suffix}"
            shutil.copy2(path, backup_path)
            self._cleanup_old_backups(backup_dir, stem=path.stem, max_backups=10)
        except OSError:
            self.statusBar().showMessage(
                "Warning: could not write database backup", 5000
            )

    def _cleanup_old_backups(
        self, backup_dir: Path, *, stem: str, max_backups: int = 10
    ) -> None:
        try:
            pattern = f"{stem}_*.kdbx"
            backups = sorted(
                backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime
            )
            while len(backups) > max_backups:
                oldest = backups.pop(0)
                oldest.unlink(missing_ok=True)
        except OSError:
            pass

    def _save_with_backup(self, session_id: str | None = None) -> None:
        target = session_id or self._dbm.active_id
        if target:
            self._backup_session(target)
            if self._file_watcher is not None:
                self._file_watcher.ignore_briefly(target)
        self._dbm.save(session_id)

    def _save_all_with_backup(self) -> list[str]:
        for session_id in self._dbm.dirty_session_ids():
            self._backup_session(session_id)
            if self._file_watcher is not None:
                self._file_watcher.ignore_briefly(session_id)
        return self._dbm.save_all()

    def _sync_file_watches(self) -> None:
        if self._file_watcher is None:
            return
        if not self._settings.watch_database_files:
            self._file_watcher.set_paths([])
            return
        paths: list[Path] = []
        for session_id in self._dbm.session_ids():
            path = Path(session_id)
            if path.is_file():
                paths.append(path)
        self._file_watcher.set_paths(paths)

    def _on_database_file_changed(self, path: str) -> None:
        if self._dbm.active is None:
            return
        session_id = None
        for sid in self._dbm.session_ids():
            if str(Path(sid).resolve()) == str(Path(path).resolve()):
                session_id = sid
                break
        if session_id is None:
            return
        dirty = self._dbm.display_name(session_id).endswith(" *")
        # Prefer manager dirty flag when available.
        try:
            dirty = self._dbm._get(session_id).is_dirty  # noqa: SLF001
        except Exception:
            pass
        if dirty:
            choice = QMessageBox.warning(
                self,
                tr("Database changed on disk"),
                tr(
                    "{path} was modified outside KDBXStudio while you have "
                    "unsaved changes.\n\n"
                    "Reload from disk (discard local edits), keep editing, "
                    "or cancel?"
                ).format(path=Path(path).name),
                QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Ignore
                | QMessageBox.StandardButton.Cancel,
            )
            if choice == QMessageBox.StandardButton.Discard:
                self._reload_session_from_disk(session_id)
            return
        choice = QMessageBox.information(
            self,
            tr("Database changed on disk"),
            tr(
                "{path} was modified outside KDBXStudio "
                "(for example by Syncthing).\n\nReload it now?"
            ).format(path=Path(path).name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self._reload_session_from_disk(session_id)

    def _reload_session_from_disk(self, session_id: str) -> None:
        from kdbxstudio.ui.dialogs.unlock_dialog import UnlockDialog

        path = Path(session_id)
        dialog = UnlockDialog(self, path=path, create_mode=False)
        if dialog.exec() != UnlockDialog.DialogCode.Accepted:
            return
        db_path, password, keyfile = self._consume_unlock_dialog(dialog)
        try:
            self._dbm.close(session_id)
            self._dbm.open(db_path, password=password, keyfile=keyfile)
            self.statusBar().showMessage(tr("Database reloaded from disk"), 4000)
            log_security_event("vault_reloaded", database=db_path.name)
        except (InvalidCredentialsError, DatabaseError) as exc:
            QMessageBox.critical(self, tr("Reload failed"), str(exc))
        self._sync_file_watches()
        self._sync_browser_bridge()

    def _browser_protocol_context(self):
        from kdbxstudio.browser.protocol import ProtocolContext

        def get_database():
            return self._dbm.active

        def get_entries():
            if self._dbm.active is None:
                return []
            return self._dbm.all_entries(include_recycle_bin=False)

        def list_groups():
            if self._dbm.active is None:
                return []
            return self._dbm.list_groups()

        def prompt_associate(label: str) -> str | None:
            if self._browser_bridge is None:
                return None
            return self._browser_bridge.prompt_associate_blocking(label)

        def lock_database() -> None:
            QTimer.singleShot(0, self._lock_from_browser)

        def ensure_group_path(path: str) -> str:
            return self._dbm.ensure_group_path(path)

        def add_entry(group_uuid, title, username="", password="", url="", **_kw):
            return self._dbm.add_entry(
                group_uuid,
                title=title,
                username=username,
                password=password,
                url=url,
            )

        def update_entry(uuid, **kwargs):
            from kdbxstudio.browser.protocol import _normalize_uuid

            return self._dbm.update_entry(_normalize_uuid(uuid), **kwargs)

        def get_entry(uuid):
            from kdbxstudio.browser.protocol import _normalize_uuid

            entry = self._dbm.get_entry(_normalize_uuid(uuid))
            if entry is None:
                entry = self._dbm.get_entry(uuid)
            return entry

        return ProtocolContext(
            get_database=get_database,
            get_entries=get_entries,
            list_groups=list_groups,
            prompt_associate=prompt_associate,
            lock_database=lock_database,
            ensure_group_path=ensure_group_path,
            add_entry=add_entry,
            update_entry=update_entry,
            get_entry=get_entry,
        )

    def _lock_from_browser(self) -> None:
        """Lock all vaults without prompting for unlock (browser lock-database)."""
        if not self._dbm.session_ids():
            self._sync_browser_bridge()
            return
        if self._dbm.dirty_session_ids():
            try:
                self._save_all_with_backup()
            except DatabaseError:
                pass
        if self._settings.clear_clipboard_on_lock:
            self._clipboard.cancel()
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.clear()
        self._dbm.close_all()
        self._clear_entry_panels()
        self._sync_browser_bridge()
        self.statusBar().showMessage(tr("Databases locked"), 5000)

    def _sync_browser_bridge(self) -> None:
        from kdbxstudio.browser.server import BrowserLocalServer

        enabled = getattr(self._settings, "browser_integration_enabled", True)
        if not enabled or self._dbm.active is None:
            if self._browser_bridge is not None:
                self._browser_bridge.stop()
                self._browser_bridge = None
            return
        if self._browser_bridge is None:
            self._browser_bridge = BrowserLocalServer(
                self._browser_protocol_context, parent=self
            )
            self._browser_bridge.associate_requested.connect(
                self._on_browser_associate_requested
            )
            try:
                paths = self._browser_bridge.start()
                if paths:
                    self.statusBar().showMessage(
                        tr("Browser integration ready (KeePassXC-Browser)"),
                        4000,
                    )
            except Exception:
                self._browser_bridge = None
                return
        else:
            self._browser_bridge.refresh_context()

    def _on_browser_associate_requested(self, db_label: str) -> None:
        if self._browser_bridge is None:
            return
        name, ok = QInputDialog.getText(
            self,
            tr("Browser association"),
            tr(
                "KeePassXC-Browser wants to connect to:\n{db}\n\n"
                "Give this connection a name (for example: firefox-laptop):"
            ).format(db=db_label),
            text="kdbxstudio",
        )
        if not ok or not name.strip():
            self._browser_bridge.provide_associate_id(None)
            return
        self._browser_bridge.provide_associate_id(name.strip())
        self.statusBar().showMessage(tr("Browser associated — remember to Save"), 5000)

    def close_database(self) -> None:
        if self._dbm.active is not None and self._dbm.active.is_dirty:
            answer = QMessageBox.question(
                self,
                tr("Unsaved changes"),
                tr("Save this database before closing?"),
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return
            if answer == QMessageBox.StandardButton.Save:
                try:
                    self._save_with_backup()
                except DatabaseError as exc:
                    QMessageBox.critical(self, tr("Save failed"), str(exc))
                    return
        self._dbm.close()
        self._clear_entry_panels()
        self._sync_browser_bridge()
        self.statusBar().showMessage(tr("Database closed"), 3000)

    def add_entry(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, tr("Add entry"), tr("Open a database first."))
            return
        group_uuid = self._group_tree.selected_group_uuid()
        if not group_uuid:
            group_uuid = self._dbm.root_group_uuid()
        group_path = next(
            (g.path for g in self._dbm.list_groups() if g.uuid == group_uuid),
            "Root",
        )
        dialog = NewEntryDialog(
            self,
            clipboard_guard=self._clipboard,
            group_path=group_path,
        )
        if dialog.exec() != NewEntryDialog.DialogCode.Accepted:
            return
        data = dialog.entry_data()
        from kdbxstudio.application.expiry import local_date_to_utc_end_of_day

        expiry_time = None
        if data.expires and data.expiry_date:
            try:
                expiry_time = local_date_to_utc_end_of_day(data.expiry_date)
            except ValueError:
                expiry_time = None
        try:
            entry = self._dbm.add_entry(
                group_uuid,
                title=data.title,
                username=data.username,
                password=data.password,
                url=data.url,
                notes=data.notes,
                tags=list(data.tags) or None,
                expires=data.expires if data.expires or expiry_time else None,
                expiry_time=expiry_time,
            )
            if data.otp:
                entry = self._dbm.update_entry(entry.uuid, otp=data.otp)
            self._on_group_selected(group_uuid)
            self._show_entry(entry.uuid)
            self.statusBar().showMessage(f"Added entry '{entry.title}'", 3000)
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Add failed"), str(exc))
        self._auto_lock.activity()

    def add_entry_from_template(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            QMessageBox.information(self, tr("Template"), tr("Open a database first."))
            return
        from kdbxstudio.ui.dialogs.template_dialog import TemplateDialog

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
            QMessageBox.critical(self, tr("Template failed"), str(exc))
        self._auto_lock.activity()

    def delete_entry(self, permanent: bool = False) -> None:
        if not self._ensure_writable():
            return
        uuids = self._entry_list.selected_entry_uuids()
        if not uuids and self._current_entry_uuid:
            uuids = [self._current_entry_uuid]
        if not uuids or self._dbm.active is None:
            return
        count = len(uuids)
        if permanent:
            key = (
                "Permanently delete {count} selected entry?"
                if count == 1
                else "Permanently delete {count} selected entries?"
            )
            confirm = QMessageBox.question(
                self,
                tr("Delete permanently"),
                tr(key).format(count=count),
            )
        else:
            key = (
                "Move {count} selected entry to the Recycle Bin?"
                if count == 1
                else "Move {count} selected entries to the Recycle Bin?"
            )
            confirm = QMessageBox.question(
                self,
                tr("Recycle Bin"),
                tr(key).format(count=count),
            )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            removed = self._dbm.delete_entries(uuids, permanent=permanent)
            self._clear_entry_panels()
            label = tr("entry") if removed == 1 else tr("entries")
            action = tr("Deleted") if permanent else tr("Moved to Recycle Bin")
            self.statusBar().showMessage(f"{action}: {removed} {label}", 4000)
            if not permanent:
                self._select_recycle_bin()
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Delete failed"), str(exc))
        self._auto_lock.activity()

    def _select_recycle_bin(self) -> None:
        """Focus the Recycle Bin group and list all trashed entries."""
        if self._dbm.active is None:
            return
        bin_uuid = self._dbm.recycle_bin_uuid()
        if not bin_uuid:
            return
        self._group_tree.set_groups(
            self._dbm.list_groups(),
            self._dbm.root_group_uuid(),
            select_uuid=bin_uuid,
        )
        self._on_group_selected(bin_uuid)

    def empty_recycle_bin(self) -> None:
        if not self._ensure_writable():
            return
        if self._dbm.active is None:
            return
        confirm = QMessageBox.question(
            self,
            tr("Empty Recycle Bin"),
            tr("Permanently delete all recycled entries?"),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            count = self._dbm.empty_recycle_bin()
            label = "entry" if count == 1 else "entries"
            self.statusBar().showMessage(
                f"Removed {count} recycled {label}", 4000
            )
            self._select_recycle_bin()
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Empty bin failed"), str(exc))
        self._auto_lock.activity()

    def open_security_settings(self) -> None:
        from kdbxstudio.ui.dialogs.security_settings_dialog import (
            SecuritySettingsDialog,
        )

        previous_language = get_language()
        dialog = SecuritySettingsDialog(
            self._settings,
            self,
            on_accent_preview=lambda a: self._preview_accent(a),
        )
        if dialog.exec() != SecuritySettingsDialog.DialogCode.Accepted:
            # Restore appearance if user cancelled after live accent preview.
            self._apply_appearance()
            return
        self._settings = dialog.result_settings()
        save_settings(self._settings)
        self._clipboard.set_timeout(self._settings.clipboard_timeout_ms)
        self._auto_lock.set_timeout(self._settings.auto_lock_timeout_ms)
        self._auto_lock.set_enabled(self._settings.auto_lock_enabled)
        self._apply_ui_density()
        self._apply_appearance()
        self._apply_window_resolution()
        set_language(self._settings.language)
        language_changed = get_language() != previous_language
        if language_changed:
            self._retranslate_shell()
        self._sync_file_watches()
        self._sync_browser_bridge()
        self.statusBar().showMessage(tr("Settings saved"), 3000)
        if language_changed:
            QMessageBox.information(
                self,
                tr("Language"),
                tr(
                    "Some remaining labels may need an application "
                    "restart to update."
                ),
            )
        self._auto_lock.activity()

    def open_plugins(self) -> None:
        from kdbxstudio.ui.dialogs.plugin_marketplace_dialog import (
            PluginMarketplaceDialog,
        )

        dialog = PluginMarketplaceDialog(self._plugins, self)
        dialog.exec()

    def open_installed_plugins(self) -> None:
        from kdbxstudio.ui.dialogs.plugin_dialog import PluginDialog

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
        self.statusBar().showMessage(tr("{n} result(s)").format(n=len(hits)), 3000)
        self._auto_lock.activity()

    def _on_search_text_changed(self, text: str) -> None:
        # Clear button (×) empties the field without Enter — restore group list.
        if text.strip():
            return
        if self._dbm.active is None:
            return
        self._run_search()

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
            if self._audit_dialog is not None:
                self._audit_dialog.view_model.clear()
                self._audit_dialog.hide()
            self._groups_dock.hide()
            self.setWindowTitle(f"KDBXStudio {__version__}")
            return
        self._groups_dock.show()
        self._stack.setCurrentWidget(self._workspace_widget)
        name = self._dbm.display_name()
        self.setWindowTitle(f"KDBXStudio — {name}")
        selected_group = self._group_tree.selected_group_uuid()
        groups = self._dbm.list_groups()
        root = self._dbm.root_group_uuid()
        group_ids = {g.uuid for g in groups}
        target = (
            selected_group
            if selected_group and selected_group in group_ids
            else root
        )
        self._group_tree.set_groups(groups, root, select_uuid=target)
        query = self._search_box.text().strip()
        filt = self._filter_bar.current_filter(query=query)
        self._active_filter = filt
        target_is_bin = any(g.uuid == target and g.is_recycle_bin for g in groups)
        # Recycle Bin selection always shows bin contents — do not let an active
        # search/filter strip recycled entries while the bin group is selected.
        if target_is_bin:
            self._on_group_selected(target)
        elif query or not filt.is_empty():
            self._run_search()
        else:
            self._on_group_selected(target)
        self._schedule_audit()
        self._sync_file_watches()
        self._sync_browser_bridge()

    def _schedule_audit(self) -> None:
        dialog = self._audit_dialog
        if dialog is None or not dialog.isVisible():
            return
        self._audit_timer.start()

    def _run_debounced_audit(self) -> None:
        dialog = self._audit_dialog
        if dialog is None or not dialog.isVisible():
            return
        self._refresh_audit(include_hibp=False)

    def _ensure_audit_dialog(self):
        if self._audit_dialog is None:
            from kdbxstudio.ui.security_dashboard import SecurityDashboardDialog

            self._audit_dialog = SecurityDashboardDialog(self)
            vm = self._audit_dialog.view_model
            vm.refresh_requested.connect(self._refresh_audit)
            vm.entry_activated.connect(self._on_finding_activated)
            vm.fix_next_requested.connect(self._on_fix_next_finding)
            self._audit_dialog.dashboard.set_hidden_panels(
                self._settings.dashboard_hidden_panels
            )
        return self._audit_dialog

    def _on_fix_next_finding(self, kind: str, entry_uuid: str) -> None:
        # Prefer guided wizard when the dashboard has a full findings list.
        dialog = self._audit_dialog
        findings = []
        if dialog is not None and dialog.view_model.snapshot is not None:
            findings = list(dialog.view_model.snapshot.findings)
        actionable = [f for f in findings if getattr(f, "entry_uuid", None)]
        if len(actionable) > 1:
            wizard = HealthFixWizardDialog(actionable, self)
            wizard.open_entry.connect(self._on_finding_activated)
            wizard.fix_entry.connect(self._apply_finding_fix)
            wizard.exec()
            if hasattr(dialog, "dashboard"):
                csv = dialog.dashboard.hidden_panels_csv()
                if csv != self._settings.dashboard_hidden_panels:
                    self._settings = self._settings.with_updates(
                        dashboard_hidden_panels=csv
                    )
                    save_settings(self._settings)
            return
        self._apply_finding_fix(kind, entry_uuid)

    def _apply_finding_fix(self, kind: str, entry_uuid: str) -> None:
        self._on_finding_activated(entry_uuid)
        tips = {
            "empty_password": tr("Generate or enter a strong password, then Save."),
            "weak_password": tr("Use Generate for a stronger password, then Save."),
            "low_entropy": tr("Prefer a longer generated password, then Save."),
            "pwned_password": tr(
                "This password appears in breaches — generate a new one."
            ),
            "expired": tr("Update the expiry date or renew the credential."),
            "expiring_soon": tr("Renew before expiry or extend the date."),
            "duplicate_password": tr(
                "Replace the shared password with a unique generated one."
            ),
        }
        tip = tips.get(kind, tr("Review and update this entry."))
        self._show_status_message(tip, 8000)
        if kind in {
            "empty_password",
            "weak_password",
            "low_entropy",
            "pwned_password",
            "duplicate_password",
        }:
            self._entry_tabs.setCurrentWidget(self._entry_detail)
            self.open_password_generator()

    def open_security_dashboard(self) -> None:
        dialog = self._ensure_audit_dialog()
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        self._refresh_audit()

    def open_password_health(self) -> None:
        """Backwards-compatible alias for Security Dashboard."""
        self.open_security_dashboard()

    def _refresh_audit(self, *, include_hibp: bool | None = None) -> None:
        dialog = self._audit_dialog
        if self._dbm.active is None:
            if dialog is not None:
                dialog.view_model.clear()
            return
        check_hibp = (
            self._settings.hibp_enabled
            if include_hibp is None
            else include_hibp
        )
        # Local checks stay on the UI thread; HIBP runs in a worker.
        report = self._audit.run(check_hibp=False)
        snapshot = self._security_analyzer.run(audit_report=report)
        if dialog is not None:
            dialog.view_model.set_snapshot(snapshot)
        tones: dict[str, str] = {}
        for finding in report.findings:
            if not finding.entry_uuid:
                continue
            tone = (
                "danger"
                if finding.severity == "critical"
                else "warning"
                if finding.severity == "warning"
                else "muted"
            )
            prev = tones.get(finding.entry_uuid)
            if prev == "danger":
                continue
            if prev == "warning" and tone == "muted":
                continue
            tones[finding.entry_uuid] = tone
        self._entry_list.set_audit_tones(tones)
        self._plugins.context.emit("audit.completed", report=report)
        self._auto_lock.activity()
        if not check_hibp:
            return
        entries = self._dbm.all_entries(include_recycle_bin=False)
        self._audit_hibp_generation += 1
        generation = self._audit_hibp_generation
        base_report = report

        def _worker() -> None:
            findings, pwned = AuditEngine.hibp_findings_for_entries(entries)
            merged = replace(
                base_report,
                findings=base_report.findings + tuple(findings),
                pwned=pwned,
            )
            if generation == self._audit_hibp_generation:
                self._audit_hibp_done.emit(merged)

        Thread(target=_worker, daemon=True).start()

    def _on_audit_hibp_done(self, report: object) -> None:
        if not isinstance(report, AuditReport):
            return
        dialog = self._audit_dialog
        if dialog is None or not dialog.isVisible():
            return
        snapshot = self._security_analyzer.run(audit_report=report)
        dialog.view_model.set_snapshot(snapshot)
        self._plugins.context.emit("audit.completed", report=report)

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
        self._attachments.set_attachments(
            self._dbm.list_attachments(entry_uuid, include_data=False)
        )
        self._pem.inspect_entry(entry)
        if (entry.url or "").strip():
            self._maybe_fetch_favicon(entry.url)

    def _load_attachment_bytes(self, attachment_id: int) -> bytes:
        if not self._current_entry_uuid or self._dbm.active is None:
            return b""
        return self._dbm.get_attachment_data(
            self._current_entry_uuid, attachment_id
        )

    def _maybe_fetch_favicon(self, url: str) -> None:
        had_cache = cached_favicon(url) is not None
        if had_cache or self._dbm.active is None:
            return

        def _fetch() -> None:
            try:
                fetch_favicon(url)
            except Exception:
                pass
            self._favicon_ready.emit()

        Thread(target=_fetch, daemon=True).start()

    def _prefetch_entry_favicons(self, urls: object) -> None:
        if self._dbm.active is None or not isinstance(urls, list):
            return
        prefetch_favicons(
            [str(u) for u in urls],
            on_done=lambda: self._favicon_ready.emit(),
        )

    def _on_favicon_fetched(self) -> None:
        if self._dbm.active is None:
            return
        self._entry_list.refresh_icons()

    def _attach_file(self, path: Path | str) -> str:
        """Attach a regular file. Returns 'attached', 'skipped', or 'failed'."""
        if not self._current_entry_uuid or self._dbm.active is None:
            return "failed"
        file_path = resolve_regular_file(path)
        if file_path is None:
            return "skipped"
        max_bytes = 25 * 1024 * 1024
        try:
            size = file_path.stat().st_size
            if size > max_bytes:
                QMessageBox.warning(
                    self,
                    "Attachment too large",
                    f"{file_path.name} exceeds the 25 MiB limit.",
                )
                return "skipped"
            data = file_path.read_bytes()
            self._dbm.add_attachment(
                self._current_entry_uuid, file_path.name, data
            )
            return "attached"
        except (OSError, DatabaseError) as exc:
            QMessageBox.critical(self, tr("Attachment failed"), str(exc))
            return "failed"

    def _on_files_dropped(self, paths: object) -> None:
        if not self._ensure_writable():
            return
        if not self._current_entry_uuid or self._dbm.active is None:
            return
        if not isinstance(paths, list):
            return
        attached = 0
        for item in paths:
            result = self._attach_file(str(item))
            if result == "attached":
                attached += 1
            elif result == "failed":
                break
        if attached and self._current_entry_uuid:
            self._show_entry(self._current_entry_uuid)
            self.statusBar().showMessage(f"Attached {attached} file(s)", 3000)
        self._auto_lock.activity()

    def _add_attachment(self) -> None:
        if not self._ensure_writable():
            return
        if not self._current_entry_uuid or self._dbm.active is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Add Attachment"), str(Path.home()), tr("All Files (*)")
        )
        if not path:
            return
        if self._attach_file(path) == "attached":
            self._show_entry(self._current_entry_uuid)
            self.statusBar().showMessage(f"Attached {Path(path).name}", 3000)
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
            QMessageBox.critical(self, tr("Remove failed"), str(exc))
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
        if not session_id:
            return
        if session_id in self._dbm.dirty_session_ids():
            answer = QMessageBox.question(
                self,
                tr("Unsaved changes"),
                tr("Save this database before closing?"),
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return
            if answer == QMessageBox.StandardButton.Save:
                try:
                    self._save_with_backup(session_id)
                except DatabaseError as exc:
                    QMessageBox.critical(self, tr("Save failed"), str(exc))
                    return
        self._dbm.close(session_id)
        if self._dbm.active is None:
            self._clear_entry_panels()

    def _on_group_selected(self, group_uuid: str) -> None:
        if self._dbm.active is None:
            return
        # Recycle Bin lists nested trashed groups recursively (pykeepass default).
        recursive: bool | None = None
        for group in self._dbm.list_groups():
            if group.uuid == group_uuid and group.is_recycle_bin:
                recursive = True
                break
        entries = self._dbm.list_entries(
            group_uuid, recursive=recursive, include_secrets=False
        )
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
            self.raise_()
            self.activateWindow()

    def _on_save_entry(self, data: dict) -> None:
        if not self._ensure_writable():
            return
        from kdbxstudio.application.expiry import local_date_to_utc_end_of_day

        expiry_time = None
        expires = data.get("expires")
        expiry_raw = data.get("expiry_time") or ""
        if expires and expiry_raw:
            try:
                expiry_time = local_date_to_utc_end_of_day(str(expiry_raw))
            except ValueError:
                expiry_time = local_date_to_utc_end_of_day(
                    datetime.now().date().isoformat()
                )
        tags = data.get("tags")
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
                tags=list(tags) if tags is not None else None,
                expires=bool(expires) if expires is not None else None,
                expiry_time=expiry_time,
            )
            group_uuid = self._group_tree.selected_group_uuid()
            if group_uuid:
                self._on_group_selected(group_uuid)
            self._show_entry(entry.uuid)
            self.statusBar().showMessage(
                "Entry updated (history saved; save database to persist)", 4000
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Update failed"), str(exc))
        self._auto_lock.activity()

    def _on_copy_password(self, password: str) -> None:
        self._clipboard.copy(password)
        secs = self._settings.clipboard_timeout_ms // 1000
        self.statusBar().showMessage(tr("Password copied (clears in {secs}s)").format(secs=secs), 3000)
        self._auto_lock.activity()

    def _on_auto_lock(self) -> None:
        if not self._dbm.session_ids():
            return
        if self._dbm.dirty_session_ids():
            try:
                self._save_all_with_backup()
            except DatabaseError as exc:
                QMessageBox.critical(
                    self,
                    "Auto-lock aborted",
                    f"Could not save before locking:\n{exc}",
                )
                self._auto_lock.activity()
                return
        paths = self._dbm.session_paths()
        if self._settings.clear_clipboard_on_lock:
            self._clipboard.cancel()
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.clear()
        self._dbm.close_all()
        self._clear_entry_panels()
        self._sync_browser_bridge()
        self._set_tray_locked(True)
        self._show_status_message(tr("Databases locked"), 5000)
        log_security_event("vault_locked", databases=len(paths))
        if self._settings.minimize_on_lock:
            self.showMinimized()
            if self._tray is not None:
                self.hide()
        for path in paths:
            dialog = UnlockDialog(self, path=path, create_mode=False)
            if dialog.exec() != UnlockDialog.DialogCode.Accepted:
                continue
            db_path, password, keyfile = self._consume_unlock_dialog(dialog)
            try:
                self._dbm.open(db_path, password=password, keyfile=keyfile)
                log_security_event("vault_unlocked", database=db_path.name)
                self._set_tray_locked(False)
            except (InvalidCredentialsError, DatabaseError) as exc:
                QMessageBox.critical(self, tr("Unlock failed"), str(exc))
                log_security_event("vault_unlock_failed", database=db_path.name)
        self._auto_lock.activity()

    def _sample_foreign_window_title(self) -> None:
        from kdbxstudio.application.autotype import active_window_title

        title = active_window_title()
        if not title:
            return
        lower = title.lower()
        if "kdbxstudio" in lower:
            return
        self._last_foreign_window_title = title

    def auto_type_selected(self) -> None:
        from kdbxstudio.application.autotype import (
            AutoTypeError,
            active_window_title,
            detect_backend,
            expand_sequence,
            find_best_entry_for_window,
            run_autotype_steps,
        )

        if self._dbm.active is None:
            QMessageBox.information(self, tr("Auto-Type"), tr("Open a database first."))
            return
        if detect_backend() is None:
            QMessageBox.warning(
                self,
                tr("Auto-Type"),
                tr("No Auto-Type backend found. Install xdotool, ydotool, or wtype."),
            )
            return

        uuid = self._entry_list.selected_entry_uuid() or self._current_entry_uuid
        matched_label = ""
        if not uuid and self._settings.autotype_match_window:
            # Prefer last non-app window (hotkey often focuses us first).
            window_title = self._last_foreign_window_title or active_window_title()
            match = find_best_entry_for_window(
                self._dbm.all_entries(include_recycle_bin=False),
                window_title,
            )
            if match is not None:
                uuid = match.entry.uuid
                matched_label = f"{match.entry.title} ({match.reason})"
                self._show_entry(uuid)
        if not uuid:
            QMessageBox.information(
                self,
                tr("Auto-Type"),
                tr(
                    "Select an entry first, or enable window matching in Settings "
                    "and focus a related application window."
                ),
            )
            return
        entry = self._dbm.get_entry(uuid)
        if entry is None:
            return
        delay_ms = self._settings.autotype_initial_delay_ms
        if matched_label:
            self.statusBar().showMessage(
                tr("Auto-Type match: {label}").format(label=matched_label),
                3000,
            )
        else:
            delay_ms, ok = QInputDialog.getInt(
                self,
                tr("Auto-Type"),
                tr(
                    "Focus the target window, then confirm.\n"
                    "Delay before typing (ms):"
                ),
                delay_ms,
                0,
                15000,
                100,
            )
            if not ok:
                return
        totp_code = ""
        if entry.otp:
            status = current_totp(entry.otp)
            totp_code = status.code or ""
        steps = expand_sequence(
            self._settings.autotype_sequence,
            username=entry.username,
            password=entry.password,
            totp=totp_code,
            url=entry.url,
        )
        self.statusBar().showMessage(tr("Focus target window… Auto-Type starting"), 2000)
        QApplication.processEvents()

        def _run() -> None:
            try:
                backend = run_autotype_steps(steps)
                self._status_message.emit(
                    f"Auto-Type completed via {backend}", 4000
                )
            except AutoTypeError as exc:
                self._autotype_failed.emit(str(exc))
            except Exception:
                self._autotype_failed.emit(
                    tr(
                        "Auto-Type failed unexpectedly. "
                        "Secrets were not shown in this dialog."
                    )
                )
            self._auto_lock.activity()

        if delay_ms > 0:
            QTimer.singleShot(delay_ms, _run)
        else:
            _run()

    def _on_autotype_failed(self, message: str) -> None:
        QMessageBox.critical(self, tr("Auto-Type failed"), message)

    def move_selected_entry(self) -> None:
        if not self._ensure_writable():
            return
        uuid = self._entry_list.selected_entry_uuid() or self._current_entry_uuid
        if not uuid or self._dbm.active is None:
            QMessageBox.information(self, tr("Move Entry"), tr("Select an entry first."))
            return
        groups = [
            g for g in self._dbm.list_groups() if not g.is_recycle_bin
        ]
        if not groups:
            return
        labels = [g.path for g in groups]
        choice, ok = QInputDialog.getItem(
            self, tr("Move Entry"), tr("Target group:"), labels, 0, False
        )
        if not ok or not choice:
            return
        target = next((g for g in groups if g.path == choice), None)
        if target is None:
            return
        self._move_entry_to_group(uuid, target.uuid)

    def _on_entry_dropped_on_group(self, entry_uuid: str, group_uuid: str) -> None:
        if not self._ensure_writable():
            return
        self._move_entry_to_group(entry_uuid, group_uuid)

    def _move_entry_to_group(self, entry_uuid: str, group_uuid: str) -> None:
        if self._dbm.active is None:
            return
        try:
            entry = self._dbm.move_entry(entry_uuid, group_uuid)
            self._on_group_selected(group_uuid)
            self._show_entry(entry.uuid)
            group = next(
                (g for g in self._dbm.list_groups() if g.uuid == group_uuid),
                None,
            )
            path = group.path if group is not None else group_uuid
            self.statusBar().showMessage(
                f"Moved '{entry.title}' to {path}", 4000
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, tr("Move failed"), str(exc))
        self._auto_lock.activity()

    def fetch_selected_favicon(self) -> None:
        uuid = self._entry_list.selected_entry_uuid() or self._current_entry_uuid
        if not uuid or self._dbm.active is None:
            QMessageBox.information(self, tr("Favicon"), tr("Select an entry first."))
            return
        entry = self._dbm.get_entry(uuid)
        if entry is None or not (entry.url or "").strip():
            QMessageBox.information(self, tr("Favicon"), tr("Selected entry has no URL."))
            return
        url = entry.url
        self.statusBar().showMessage(tr("Fetching favicon…"), 4000)

        def _fetch() -> None:
            try:
                path = fetch_favicon(url)
            except Exception as exc:
                self._favicon_manual_done.emit("", str(exc))
                return
            if path is None:
                self._favicon_manual_done.emit("", "")
                return
            self._favicon_manual_done.emit(path.name, "")

        Thread(target=_fetch, daemon=True).start()
        self._auto_lock.activity()

    def _on_favicon_manual_done(self, path_name: str, error: str) -> None:
        if error:
            QMessageBox.warning(
                self,
                tr("Favicon"),
                tr("Could not fetch favicon: {exc}").format(exc=error),
            )
            return
        if not path_name:
            QMessageBox.information(
                self, tr("Favicon"), tr("No favicon found for this URL.")
            )
            return
        self._on_favicon_fetched()
        self.statusBar().showMessage(f"Favicon saved: {path_name}", 4000)

    def merge_database(self) -> None:
        from kdbxstudio.application.merge import merge_databases
        if not self._ensure_writable():
            return
        destination = self._dbm.active
        if destination is None:
            QMessageBox.information(self, tr("Merge"), tr("Open a destination database first."))
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Merge Database",
            str(Path.home()),
            "KeePass Database (*.kdbx)",
        )
        if not path:
            return
        source_path = Path(path)
        dialog = UnlockDialog(self, path=source_path, create_mode=False)
        if dialog.exec() != UnlockDialog.DialogCode.Accepted:
            return
        db_path, password, keyfile = self._consume_unlock_dialog(dialog)
        source = KdbxDatabase()
        try:
            source.open(db_path, password=password, keyfile=keyfile)
            update = QMessageBox.question(
                self,
                "Merge options",
                "Update existing entries that match title/username/URL?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            result = merge_databases(
                destination,
                source,
                update_existing=update == QMessageBox.StandardButton.Yes,
            )
            self._dbm.refresh(self._dbm.active_id)
            self.statusBar().showMessage(
                f"Merge complete: {result.added} added, "
                f"{result.skipped} skipped, {result.updated} updated",
                8000,
            )
        except InvalidCredentialsError:
            QMessageBox.critical(self, tr("Merge failed"), tr("Invalid password or key file."))
        except (DatabaseError, OSError) as exc:
            QMessageBox.critical(self, tr("Merge failed"), str(exc))
        finally:
            source.close()
        self._auto_lock.activity()

    def export_emergency_sheet(self) -> None:
        from kdbxstudio.application.emergency_sheet import write_emergency_html

        if self._dbm.active is None:
            QMessageBox.information(self, tr("Emergency Sheet"), tr("Open a database first."))
            return
        choice = QMessageBox.question(
            self,
            tr("Emergency Sheet"),
            "Include all entries?\n\nYes = all entries · No = selected entry only",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Cancel:
            return
        if choice == QMessageBox.StandardButton.Yes:
            entries = self._dbm.all_entries(include_recycle_bin=False)
        else:
            uuid = self._entry_list.selected_entry_uuid() or self._current_entry_uuid
            if not uuid:
                QMessageBox.information(
                    self, tr("Emergency Sheet"), tr("Select an entry first.")
                )
                return
            entry = self._dbm.get_entry(uuid)
            if entry is None:
                return
            entries = [entry]
        confirm = QMessageBox.warning(
            self,
            "Includes secrets",
            "The emergency sheet may include passwords in clear text. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            tr("Save Emergency Sheet"),
            str(Path.home() / "kdbxstudio-emergency.html"),
            tr("HTML Files (*.html)"),
        )
        if not path_str:
            return
        try:
            out = write_emergency_html(path_str, entries)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(out.resolve())))
            self.statusBar().showMessage(f"Emergency sheet: {out}", 6000)
        except OSError as exc:
            QMessageBox.critical(self, tr("Emergency sheet failed"), str(exc))
        self._auto_lock.activity()

    @staticmethod
    def _extract_private_pem(text: str) -> str | None:
        pattern = re.compile(
            r"-----BEGIN ([A-Z0-9 ]+)-----\r?\n(.+?)\r?\n-----END \1-----",
            re.DOTALL,
        )
        for match in pattern.finditer(text or ""):
            label = match.group(1).upper()
            if "PRIVATE KEY" in label:
                return match.group(0).strip() + "\n"
        return None

    def add_selected_pem_to_agent(self) -> None:
        from kdbxstudio.application.ssh_agent import (
            SshAgentError,
            add_private_key,
            agent_available,
        )
        from kdbxstudio.core.pem_inspector import inspect_pem_text
        uuid = self._entry_list.selected_entry_uuid() or self._current_entry_uuid
        if not uuid or self._dbm.active is None:
            QMessageBox.information(self, tr("SSH Agent"), tr("Select an entry first."))
            return
        entry = self._dbm.get_entry(uuid)
        if entry is None:
            return
        chunks = [entry.notes, entry.password, entry.username]
        chunks.extend(entry.custom_properties.values())
        text = "\n".join(chunks)
        blocks = inspect_pem_text(text)
        if not any(b.kind == "private_key" for b in blocks):
            QMessageBox.information(
                self,
                tr("SSH Agent"),
                "No private key PEM found in the selected entry.",
            )
            return
        if not agent_available():
            QMessageBox.warning(
                self,
                tr("SSH Agent"),
                "ssh-add is unavailable or SSH_AUTH_SOCK is not set.",
            )
            return
        pem = self._extract_private_pem(text)
        if not pem:
            QMessageBox.warning(self, tr("SSH Agent"), tr("Could not extract private key PEM."))
            return
        try:
            message = add_private_key(pem)
            self.statusBar().showMessage(message or tr("Identity added to SSH agent"), 5000)
        except SshAgentError as exc:
            QMessageBox.critical(self, tr("SSH Agent"), str(exc))
        self._auto_lock.activity()

    def _about(self) -> None:
        QMessageBox.about(
            self,
            tr("About KDBXStudio"),
            (
                f"<b>KDBXStudio</b> {__version__}<br>"
                "Modern Qt6 KDBX password manager for Linux.<br>"
                f"{tr('Version')}: <b>{__version__}</b><br>"
                "License: <b>GPL-3.0-or-later</b><br><br>"
                "<b>Cuma KURT</b><br>"
                '<a href="mailto:cumakurt@gmail.com">cumakurt@gmail.com</a><br>'
                '<a href="https://www.linkedin.com/in/cuma-kurt-34414917/">'
                "LinkedIn</a> · "
                '<a href="https://github.com/cumakurt/kdbxstudio">GitHub</a>'
                f"<br><br>{tr('Use Tools → Check for Updates… to compare with GitHub.')}"
            ),
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        # Window close (title-bar X) always quits. Tray is for show/lock only —
        # hiding on close left the process running in the background.
        dirty_ids = self._dbm.dirty_session_ids()
        if dirty_ids:
            answer = QMessageBox.question(
                self,
                tr("Unsaved changes"),
                tr(
                    "Save {count} database(s) with unsaved changes before quitting?"
                ).format(count=len(dirty_ids)),
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                self._quitting = False
                event.ignore()
                return
            if answer == QMessageBox.StandardButton.Save:
                try:
                    self._save_all_with_backup()
                except DatabaseError as exc:
                    QMessageBox.critical(self, tr("Save failed"), str(exc))
                    self._quitting = False
                    event.ignore()
                    return
        self._quitting = True
        self._dbm.close_all()
        self._auto_lock.stop()
        if self._tray is not None:
            self._tray.hide()
            self._tray.setVisible(False)
        self._persist_layout()
        save_settings(self._settings)
        event.accept()
        super().closeEvent(event)
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def save_layout(self) -> None:
        self._persist_layout()
        save_settings(self._settings)
        self.statusBar().showMessage(tr("Layout saved"), 3000)

    def reset_layout(self) -> None:
        self.restoreGeometry(self._default_geometry)
        self.restoreState(self._default_state)
        self._settings = self._settings.with_updates(
            window_geometry="",
            window_state="",
        )
        save_settings(self._settings)
        self.statusBar().showMessage(tr("Layout reset"), 3000)

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
        self.setMinimumSize(640, 400)
        if initial and not self._settings.window_geometry:
            if not self._apply_window_resolution():
                self.resize(size)
                if screen is not None:
                    geo = screen.availableGeometry()
                    self.move(
                        geo.x() + max(0, (geo.width() - size.width()) // 2),
                        geo.y() + max(0, (geo.height() - size.height()) // 2),
                    )

    def _apply_window_resolution(self) -> bool:
        """Resize main window to the configured resolution preset.

        Returns True when a fixed preset was applied.
        """
        from kdbxstudio.ui.theme.geometry import window_size_for_resolution

        preset = window_size_for_resolution(self._settings.window_resolution)
        if preset is None:
            return False
        width, height = preset
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            width = min(width, max(640, avail.width() - 32))
            height = min(height, max(400, avail.height() - 32))
            self.resize(width, height)
            self.move(
                avail.x() + max(0, (avail.width() - width) // 2),
                avail.y() + max(0, (avail.height() - height) // 2),
            )
        else:
            self.resize(width, height)
        return True

    def _apply_chrome_scale(self) -> None:
        from kdbxstudio.ui.theme.manager import current_font_size, current_ui_scale

        scale = current_ui_scale()
        self.setMinimumSize(scale.px(640), scale.px(400))
        icon = scale.px(20)
        if self._main_toolbar is not None:
            self._main_toolbar.setIconSize(QSize(icon, icon))
            for child in self._main_toolbar.findChildren(QToolButton):
                child.setIconSize(QSize(icon, icon))
                child.setFixedSize(icon + 10, icon + 10)
        if hasattr(self, "_groups_dock"):
            self._groups_dock.setMinimumWidth(scale.px(140))
            self._groups_dock.setMaximumWidth(scale.px(280))
        menu = self.menuBar()
        if menu is not None:
            menu.setNativeMenuBar(False)
            font = menu.font()
            font.setPixelSize(scale.font_px(current_font_size()))
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
