"""Guided health-fix wizard over audit findings."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from kdbxstudio.application.audit_engine import AuditFinding
from kdbxstudio.i18n import tr, trf
from kdbxstudio.ui.widgets.dialog_shell import DialogShell
from kdbxstudio.ui.widgets.status_chip import StatusChip

_PASSWORD_KINDS = frozenset(
    {
        "empty_password",
        "weak_password",
        "low_entropy",
        "pwned_password",
        "duplicate_password",
    }
)


class HealthFixWizardDialog(DialogShell):
    open_entry = Signal(str)
    fix_entry = Signal(str, str)
    finished_wizard = Signal()

    def __init__(
        self,
        findings: list[AuditFinding] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
            title=tr("Health Fix Wizard"),
            subtitle=tr("Walk through security findings one by one"),
            icon_name="dashboard",
            width=520,
        )
        self._findings: list[AuditFinding] = []
        self._index = 0

        self._step = QLabel()
        self._step.setObjectName("dialogSubtitle")
        self._kind = StatusChip(object_name="statusChip")
        self._message = QLabel()
        self._message.setWordWrap(True)

        self.body.addWidget(self._step)
        self.body.addWidget(self._kind)
        self.body.addWidget(self._message)

        skip = QPushButton(tr("Skip"))
        skip.setProperty("cssClass", "secondary")
        skip.clicked.connect(self._skip)
        open_btn = QPushButton(tr("Open entry"))
        open_btn.setProperty("cssClass", "secondary")
        open_btn.clicked.connect(self._open)
        fix_btn = QPushButton(tr("Fix"))
        fix_btn.setProperty("cssClass", "primary")
        fix_btn.clicked.connect(self._fix)
        self._fix_btn = fix_btn

        row = QHBoxLayout()
        row.addWidget(skip)
        row.addWidget(open_btn)
        row.addStretch(1)
        row.addWidget(fix_btn)
        self.body.addLayout(row)

        self.set_primary_text(tr("Done"))
        self.button_box.accepted.disconnect()
        self.button_box.accepted.connect(self._done)

        if findings:
            self.set_findings(findings)

    def set_findings(self, findings: list[AuditFinding]) -> None:
        actionable = [f for f in findings if f.entry_uuid]
        self._findings = actionable
        self._index = 0
        self._render()

    def _current(self) -> AuditFinding | None:
        if 0 <= self._index < len(self._findings):
            return self._findings[self._index]
        return None

    def _render(self) -> None:
        finding = self._current()
        if finding is None:
            self._step.setText(tr("All findings reviewed"))
            self._kind.clear_chip()
            self._message.setText(tr("No more actionable findings."))
            self._fix_btn.setEnabled(False)
            return
        total = len(self._findings)
        self._step.setText(
            trf("Finding {n} of {total}", n=self._index + 1, total=total)
        )
        tone = "danger" if finding.severity == "critical" else "warning"
        self._kind.set_chip(finding.kind.replace("_", " "), tone)
        self._message.setText(finding.message)
        self._fix_btn.setEnabled(True)
        self._fix_btn.setText(
            tr("Generate password") if finding.kind in _PASSWORD_KINDS else tr("Fix")
        )

    def _advance(self) -> None:
        self._index += 1
        if self._index >= len(self._findings):
            self._render()
            return
        self._render()

    def _skip(self) -> None:
        self._advance()

    def _open(self) -> None:
        finding = self._current()
        if finding and finding.entry_uuid:
            self.open_entry.emit(finding.entry_uuid)

    def _fix(self) -> None:
        finding = self._current()
        if finding and finding.entry_uuid:
            self.fix_entry.emit(finding.kind, finding.entry_uuid)
            self._advance()

    def _done(self) -> None:
        self.finished_wizard.emit()
        self.accept()
