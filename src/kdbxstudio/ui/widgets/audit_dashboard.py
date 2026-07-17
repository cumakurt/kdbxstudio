"""Password Health Dashboard dock widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.application.audit_engine import AuditReport


class AuditDashboardWidget(QWidget):
    """Shows password health summary and findings."""

    refresh_requested = Signal()
    finding_activated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._summary = QLabel("No database open")
        self._summary.setWordWrap(True)
        self._strip = QLabel("")
        self._strip.setObjectName("auditSummaryStrip")
        self._strip.setVisible(False)

        self._health_bar = QProgressBar()
        self._health_bar.setRange(0, 100)
        self._health_bar.setValue(0)
        self._health_bar.setTextVisible(True)
        self._health_bar.setMaximumHeight(20)
        self._health_bar.setFormat("Health: %p%")
        self._health_bar.setVisible(False)

        self._stats_label = QLabel("")
        self._stats_label.setWordWrap(True)
        self._stats_label.setVisible(False)

        self._expiry_warning = QLabel("")
        self._expiry_warning.setWordWrap(True)
        self._expiry_warning.setObjectName("expiryWarning")
        self._expiry_warning.setVisible(False)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Severity", "Finding"])
        self._tree.setRootIsDecorated(False)
        self._tree.itemDoubleClicked.connect(self._on_item)

        refresh = QPushButton("Refresh audit")
        refresh.setAccessibleName("Refresh password audit")
        refresh.clicked.connect(self.refresh_requested.emit)

        top = QHBoxLayout()
        top.addWidget(self._summary, stretch=1)
        top.addWidget(refresh)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self._strip)
        layout.addWidget(self._health_bar)
        layout.addWidget(self._expiry_warning)
        layout.addWidget(self._stats_label)
        layout.addWidget(self._tree, stretch=1)

    def clear(self) -> None:
        self._summary.setText("No database open")
        self._strip.clear()
        self._strip.setVisible(False)
        self._health_bar.setVisible(False)
        self._stats_label.setVisible(False)
        self._expiry_warning.setVisible(False)
        self._tree.clear()

    def show_report(self, report: AuditReport) -> None:
        counts = report.severity_counts
        ok = max(
            0,
            report.total_entries
            - report.empty_passwords
            - report.weak_passwords
            - report.low_entropy,
        )
        self._strip.setText(
            f"Critical: {counts['critical']}  ·  "
            f"Warning: {counts['warning']}  ·  "
            f"Info: {counts['info']}  ·  "
            f"Healthy: {ok}"
        )
        self._strip.setVisible(True)

        health = report.health_score
        self._health_bar.setValue(health)
        if health >= 80:
            color = "#22c55e"
        elif health >= 60:
            color = "#84cc16"
        elif health >= 40:
            color = "#eab308"
        else:
            color = "#ef4444"
        self._health_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; }}"
        )
        self._health_bar.setVisible(True)

        if report.expired > 0 or report.expiring_soon > 0:
            parts = []
            if report.expired > 0:
                parts.append(f"<b>{report.expired}</b> expired")
            if report.expiring_soon > 0:
                parts.append(f"<b>{report.expiring_soon}</b> expiring soon")
            self._expiry_warning.setText(
                f"⚠ {' and '.join(parts)} entry/entries need attention"
            )
            self._expiry_warning.setVisible(True)
        else:
            self._expiry_warning.setVisible(False)

        stats_lines = [
            f"<b>{report.total_entries}</b> entries across "
            f"<b>{report.total_groups}</b> groups",
        ]
        if report.entries_with_url > 0:
            stats_lines.append(
                f"🌐 {report.entries_with_url} with URLs"
            )
        if report.entries_with_otp > 0:
            stats_lines.append(f"🔑 {report.entries_with_otp} with TOTP")
        if report.entries_with_tags > 0:
            stats_lines.append(f"🏷 {report.entries_with_tags} with tags")
        if report.entries_with_attachments > 0:
            stats_lines.append(
                f"📎 {report.entries_with_attachments} with attachments"
            )
        if report.entries_with_custom_fields > 0:
            stats_lines.append(
                f"📋 {report.entries_with_custom_fields} with custom fields"
            )
        self._stats_label.setText(" · ".join(stats_lines))
        self._stats_label.setVisible(True)

        self._summary.setText(
            f"Entries: {report.total_entries} · "
            f"Empty: {report.empty_passwords} · "
            f"Weak: {report.weak_passwords} · "
            f"Low entropy: {report.low_entropy} · "
            f"Duplicates: {report.duplicates} · "
            f"Findings: {len(report.findings)}"
        )
        self._tree.clear()
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        sorted_findings = sorted(
            report.findings,
            key=lambda f: severity_order.get(f.severity, 3),
        )
        for finding in sorted_findings:
            item = QTreeWidgetItem([finding.severity, finding.message])
            if finding.entry_uuid:
                item.setData(0, int(Qt.ItemDataRole.UserRole), finding.entry_uuid)
            if finding.severity == "critical":
                item.setForeground(
                    0,
                    self.palette().color(self.foregroundRole()),
                )
            self._tree.addTopLevelItem(item)
        self._tree.resizeColumnToContents(0)

    def _on_item(self, item: QTreeWidgetItem, _column: int) -> None:
        uuid = item.data(0, int(Qt.ItemDataRole.UserRole))
        if uuid:
            self.finding_activated.emit(str(uuid))
