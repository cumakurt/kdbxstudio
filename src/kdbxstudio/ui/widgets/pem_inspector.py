"""SSH / certificate PEM inspector widget."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from kdbxstudio.core.database import EntryView
from kdbxstudio.core.pem_inspector import format_pem_report, inspect_pem_text


class PemInspectorWidget(QWidget):
    """Scans entry notes / custom fields for PEM material."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._summary = QLabel("Select an entry to inspect certificates or SSH keys.")
        self._summary.setWordWrap(True)
        self._report = QTextEdit()
        self._report.setReadOnly(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._summary)
        layout.addWidget(self._report)

    def clear(self) -> None:
        self._summary.setText("Select an entry to inspect certificates or SSH keys.")
        self._report.clear()

    def inspect_entry(self, entry: EntryView) -> None:
        chunks = [entry.notes, entry.password, entry.username]
        chunks.extend(entry.custom_properties.values())
        text = "\n".join(chunks)
        blocks = inspect_pem_text(text)
        if not blocks:
            self._summary.setText(
                "No certificate or SSH key material in this entry. "
                "Paste PEM into notes or custom fields."
            )
        else:
            kinds = ", ".join(sorted({b.kind for b in blocks}))
            self._summary.setText(f"Found {len(blocks)} PEM block(s): {kinds}")
        self._report.setPlainText(format_pem_report(blocks))
