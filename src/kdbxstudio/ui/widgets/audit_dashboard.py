"""Password Health Dashboard dock widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
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
        layout.addWidget(self._tree)

    def clear(self) -> None:
        self._summary.setText("No database open")
        self._strip.clear()
        self._strip.setVisible(False)
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
            f"Healthy passwords: {ok}"
        )
        self._strip.setVisible(True)
        self._summary.setText(
            f"Entries: {report.total_entries} · "
            f"Empty: {report.empty_passwords} · "
            f"Weak: {report.weak_passwords} · "
            f"Low entropy: {report.low_entropy} · "
            f"Duplicates: {report.duplicates} · "
            f"Findings: {len(report.findings)}"
        )
        self._tree.clear()
        for finding in report.findings:
            item = QTreeWidgetItem([finding.severity, finding.message])
            if finding.entry_uuid:
                item.setData(0, int(Qt.ItemDataRole.UserRole), finding.entry_uuid)
            self._tree.addTopLevelItem(item)
        self._tree.resizeColumnToContents(0)

    def _on_item(self, item: QTreeWidgetItem, _column: int) -> None:
        uuid = item.data(0, int(Qt.ItemDataRole.UserRole))
        if uuid:
            self.finding_activated.emit(str(uuid))
