"""Password Health Dashboard widget."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.application.audit_engine import AuditReport
from kdbxstudio.i18n import tr, trf
from kdbxstudio.ui.theme.manager import set_widget_tone


class AuditDashboardWidget(QWidget):
    """Shows password health summary and findings."""

    refresh_requested = Signal()
    finding_activated = Signal(str)
    fix_next_requested = Signal(str, str)  # kind, entry_uuid

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._report: AuditReport | None = None
        self._summary = QLabel(tr("No database open"))
        self._summary.setWordWrap(True)
        self._strip = QLabel("")
        self._strip.setObjectName("auditSummaryStrip")
        self._strip.setVisible(False)

        self._health_bar = QProgressBar()
        self._health_bar.setRange(0, 100)
        self._health_bar.setValue(0)
        self._health_bar.setTextVisible(True)
        self._health_bar.setMinimumHeight(22)
        self._health_bar.setFormat(tr("Health: %p%"))
        self._health_bar.setVisible(False)

        self._stats_label = QLabel("")
        self._stats_label.setWordWrap(True)
        self._stats_label.setVisible(False)

        self._expiry_warning = QLabel("")
        self._expiry_warning.setWordWrap(True)
        self._expiry_warning.setObjectName("expiryWarning")
        self._expiry_warning.setVisible(False)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels([tr("Severity"), tr("Finding")])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setSortingEnabled(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setUniformRowHeights(True)
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tree.itemDoubleClicked.connect(self._on_item)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_tree_menu)

        refresh = QPushButton(tr("Refresh audit"))
        refresh.setAccessibleName(tr("Refresh password audit"))
        refresh.clicked.connect(self.refresh_requested.emit)

        open_btn = QPushButton(tr("Open entry"))
        open_btn.setToolTip(tr("Open the selected finding's entry"))
        open_btn.clicked.connect(self._open_current)

        fix_btn = QPushButton(tr("Fix next"))
        fix_btn.setToolTip(tr("Jump to the next actionable finding"))
        fix_btn.clicked.connect(self._fix_next)

        top = QHBoxLayout()
        top.addWidget(self._summary, stretch=1)
        top.addWidget(fix_btn)
        top.addWidget(open_btn)
        top.addWidget(refresh)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top)
        layout.addWidget(self._strip)
        layout.addWidget(self._health_bar)
        layout.addWidget(self._expiry_warning)
        layout.addWidget(self._stats_label)
        layout.addWidget(self._tree, stretch=1)

    def clear(self) -> None:
        self._report = None
        self._summary.setText(tr("No database open"))
        self._strip.clear()
        self._strip.setVisible(False)
        self._health_bar.setVisible(False)
        self._stats_label.setVisible(False)
        self._expiry_warning.setVisible(False)
        self._tree.clear()

    def show_report(self, report: AuditReport) -> None:
        self._report = report
        counts = report.severity_counts
        ok = max(
            0,
            report.total_entries
            - report.empty_passwords
            - report.weak_passwords
            - report.low_entropy,
        )
        self._strip.setText(
            tr(
                "Critical: {critical}  ·  Warning: {warning}  ·  "
                "Info: {info}  ·  Healthy: {ok}"
            ).format(
                critical=counts["critical"],
                warning=counts["warning"],
                info=counts["info"],
                ok=ok,
            )
        )
        self._strip.setVisible(True)

        health = report.health_score
        self._health_bar.setValue(health)
        if health >= 60:
            tone = "success"
        elif health >= 40:
            tone = "warning"
        else:
            tone = "danger"
        set_widget_tone(self._health_bar, tone)
        self._health_bar.setVisible(True)

        if report.expired > 0 or report.expiring_soon > 0:
            parts = []
            if report.expired > 0:
                parts.append(trf("<b>{n}</b> expired", n=report.expired))
            if report.expiring_soon > 0:
                parts.append(trf("<b>{n}</b> expiring soon", n=report.expiring_soon))
            self._expiry_warning.setText(
                tr("⚠ {parts} entry/entries need attention").format(
                    parts=tr(" and ").join(parts)
                )
            )
            self._expiry_warning.setVisible(True)
        else:
            self._expiry_warning.setVisible(False)

        stats_lines = [
            trf(
                "<b>{entries}</b> entries across <b>{groups}</b> groups",
                entries=report.total_entries,
                groups=report.total_groups,
            ),
        ]
        if report.entries_with_url > 0:
            stats_lines.append(trf("🌐 {n} with URLs", n=report.entries_with_url))
        if report.entries_with_otp > 0:
            stats_lines.append(trf("🔑 {n} with TOTP", n=report.entries_with_otp))
        if report.entries_with_tags > 0:
            stats_lines.append(trf("🏷 {n} with tags", n=report.entries_with_tags))
        if report.entries_with_attachments > 0:
            stats_lines.append(
                trf(
                    "📎 {n} with attachments",
                    n=report.entries_with_attachments,
                )
            )
        if report.entries_with_custom_fields > 0:
            stats_lines.append(
                trf(
                    "📋 {n} with custom fields",
                    n=report.entries_with_custom_fields,
                )
            )
        self._stats_label.setText(" · ".join(stats_lines))
        self._stats_label.setVisible(True)

        self._summary.setText(
            tr(
                "Entries: {total} · Empty: {empty} · Weak: {weak} · "
                "Low entropy: {entropy} · Duplicates: {dupes} · "
                "Findings: {findings}"
            ).format(
                total=report.total_entries,
                empty=report.empty_passwords,
                weak=report.weak_passwords,
                entropy=report.low_entropy,
                dupes=report.duplicates,
                findings=len(report.findings),
            )
        )
        self._tree.setSortingEnabled(False)
        self._tree.clear()
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        sorted_findings = sorted(
            report.findings,
            key=lambda f: severity_order.get(f.severity, 3),
        )
        for finding in sorted_findings:
            item = QTreeWidgetItem([tr(finding.severity), finding.message])
            if finding.entry_uuid:
                item.setData(0, int(Qt.ItemDataRole.UserRole), finding.entry_uuid)
            item.setToolTip(1, finding.message)
            self._tree.addTopLevelItem(item)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self._tree.resizeColumnToContents(0)

    def _open_current(self) -> None:
        item = self._tree.currentItem()
        if item is not None:
            self._on_item(item, 0)

    def _fix_next(self) -> None:
        if self._report is None:
            return
        priority = {"critical": 0, "warning": 1, "info": 2}
        actionable = [
            f
            for f in self._report.findings
            if f.entry_uuid
            and f.kind
            in {
                "empty_password",
                "weak_password",
                "low_entropy",
                "pwned_password",
                "expired",
                "expiring_soon",
                "duplicate_password",
            }
        ]
        if not actionable:
            return
        actionable.sort(key=lambda f: priority.get(f.severity, 9))
        finding = actionable[0]
        assert finding.entry_uuid is not None
        self.fix_next_requested.emit(finding.kind, finding.entry_uuid)

    def _on_item(self, item: QTreeWidgetItem, _column: int) -> None:
        uuid = item.data(0, int(Qt.ItemDataRole.UserRole))
        if uuid:
            self.finding_activated.emit(str(uuid))

    def _show_tree_menu(self, pos: QPoint) -> None:
        item = self._tree.itemAt(pos)
        if item is not None:
            self._tree.setCurrentItem(item)
        menu = QMenu(self)
        open_entry = menu.addAction(tr("Open entry"))
        uuid = None
        if item is not None:
            uuid = item.data(0, int(Qt.ItemDataRole.UserRole))
        open_entry.setEnabled(bool(uuid))
        if uuid:
            open_entry.triggered.connect(lambda: self.finding_activated.emit(str(uuid)))
        menu.addSeparator()
        menu.addAction(tr("Refresh audit"), self.refresh_requested.emit)
        menu.exec(self._tree.mapToGlobal(pos))
