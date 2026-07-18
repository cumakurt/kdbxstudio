"""Dialog to create an entry from a secret template."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QWidget,
)

from kdbxstudio.application.templates import EntryTemplate, list_templates
from kdbxstudio.i18n import tr
from kdbxstudio.ui.theme.motion import fade_in
from kdbxstudio.ui.widgets.dialog_shell import DialogShell


class TemplateDialog(DialogShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            title=tr("New Entry from Template"),
            subtitle=tr("Start from a structured secret template"),
            icon_name="add",
            width=460,
        )
        self._anim = None
        self.resize(460, 400)
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
        form.addRow(tr("Template"), self._combo)
        form.addRow("", self._description)
        form.addRow(tr("Title"), self._title)
        self.body.addLayout(form)
        self.body.addLayout(self._fields_form)
        self.body.addWidget(QLabel(tr("Notes")))
        self.body.addWidget(self._notes)

        self.set_primary_text(tr("Create"))
        self.button_box.accepted.disconnect()
        self.button_box.accepted.connect(self._accept)
        self._on_template_changed(0)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._anim = fade_in(self)

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
