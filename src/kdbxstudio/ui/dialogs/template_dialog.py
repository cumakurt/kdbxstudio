"""Dialog to create an entry from a secret template."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.application.templates import EntryTemplate, list_templates


class TemplateDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Entry from Template")
        self.setModal(True)
        self.resize(420, 360)

        self._templates = list_templates()
        self._combo = QComboBox()
        for template in self._templates:
            self._combo.addItem(template.name, template.id)
        self._combo.currentIndexChanged.connect(self._on_template_changed)

        self._description = QLabel("")
        self._description.setWordWrap(True)
        self._title = QLineEdit()
        self._field_edits: dict[str, QLineEdit] = {}
        self._fields_form = QFormLayout()
        self._notes = QTextEdit()

        form = QFormLayout()
        form.addRow("Template", self._combo)
        form.addRow("", self._description)
        form.addRow("Title", self._title)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn is not None:
            ok_btn.setProperty("cssClass", "primary")
            ok_btn.setDefault(True)
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn is not None:
            cancel_btn.setProperty("cssClass", "secondary")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addLayout(self._fields_form)
        layout.addWidget(QLabel("Notes"))
        layout.addWidget(self._notes)
        layout.addWidget(buttons)

        self._on_template_changed(0)

    def selected_template(self) -> EntryTemplate:
        template_id = str(self._combo.currentData())
        for template in self._templates:
            if template.id == template_id:
                return template
        return self._templates[0]

    def title_value(self) -> str:
        return self._title.text().strip()

    def field_values(self) -> dict[str, str]:
        return {key: edit.text() for key, edit in self._field_edits.items()}

    def notes_value(self) -> str:
        return self._notes.toPlainText()

    def _on_template_changed(self, _index: int) -> None:
        template = self.selected_template()
        self._description.setText(template.description)
        self._title.setText(template.title_prefix)
        self._notes.setPlainText(template.notes_placeholder)
        while self._fields_form.rowCount():
            self._fields_form.removeRow(0)
        self._field_edits.clear()
        for spec in template.fields:
            edit = QLineEdit(spec.default)
            if spec.secret:
                edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._field_edits[spec.key] = edit
            self._fields_form.addRow(spec.label, edit)

    def _accept(self) -> None:
        if not self.title_value():
            self._title.setFocus()
            return
        self.accept()
