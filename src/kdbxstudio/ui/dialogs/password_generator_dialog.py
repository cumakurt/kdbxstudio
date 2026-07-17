"""Password generator dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.core.password_generator import (
    GeneratorOptions,
    build_alphabet,
    estimate_entropy_bits,
    generate_password,
)


class PasswordGeneratorDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Password Generator")
        self.setModal(True)
        self.resize(420, 280)

        self._length = QSpinBox()
        self._length.setRange(4, 128)
        self._length.setValue(20)

        self._upper = QCheckBox("Uppercase")
        self._upper.setChecked(True)
        self._lower = QCheckBox("Lowercase")
        self._lower.setChecked(True)
        self._digits = QCheckBox("Digits")
        self._digits.setChecked(True)
        self._symbols = QCheckBox("Symbols")
        self._symbols.setChecked(True)
        self._ambiguous = QCheckBox("Exclude ambiguous (O/0/Il1)")
        self._ambiguous.setChecked(True)

        self._output = QLineEdit()
        self._output.setReadOnly(True)
        self._entropy = QLabel("")

        regenerate = QPushButton("Generate")
        regenerate.clicked.connect(self._regenerate)
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(self._copy)

        out_row = QHBoxLayout()
        out_row.addWidget(self._output)
        out_row.addWidget(regenerate)
        out_row.addWidget(copy_btn)

        form = QFormLayout()
        form.addRow("Length", self._length)
        form.addRow("", self._upper)
        form.addRow("", self._lower)
        form.addRow("", self._digits)
        form.addRow("", self._symbols)
        form.addRow("", self._ambiguous)
        form.addRow("Password", out_row)
        form.addRow("Entropy", self._entropy)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        for widget in (
            self._length,
            self._upper,
            self._lower,
            self._digits,
            self._symbols,
            self._ambiguous,
        ):
            if isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self._regenerate)
            else:
                widget.toggled.connect(self._regenerate)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
        self._regenerate()

    def password(self) -> str:
        return self._output.text()

    def _options(self) -> GeneratorOptions:
        return GeneratorOptions(
            length=self._length.value(),
            uppercase=self._upper.isChecked(),
            lowercase=self._lower.isChecked(),
            digits=self._digits.isChecked(),
            symbols=self._symbols.isChecked(),
            exclude_ambiguous=self._ambiguous.isChecked(),
        )

    def _regenerate(self) -> None:
        try:
            opts = self._options()
            password = generate_password(opts)
            alphabet = build_alphabet(opts)
            bits = estimate_entropy_bits(password, len(alphabet))
            self._output.setText(password)
            self._entropy.setText(f"~{bits:.0f} bits ({len(alphabet)} symbol alphabet)")
        except ValueError as exc:
            self._output.clear()
            self._entropy.setText(str(exc))

    def _copy(self) -> None:
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._output.text())
