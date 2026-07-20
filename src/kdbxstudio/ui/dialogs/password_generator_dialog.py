"""Password generator dialog."""

from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from kdbxstudio.core.password_generator import (
    PRESETS,
    GeneratorOptions,
    build_alphabet,
    estimate_entropy_bits,
    generate_password,
)
from kdbxstudio.i18n import tr
from kdbxstudio.security.session import ClipboardGuard
from kdbxstudio.ui.theme.motion import fade_in
from kdbxstudio.ui.widgets.countdown_ring import CountdownRing
from kdbxstudio.ui.widgets.dialog_shell import DialogShell
from kdbxstudio.ui.widgets.status_chip import StatusChip


class PasswordGeneratorDialog(DialogShell):
    def __init__(
        self,
        parent: QWidget | None = None,
        clipboard_guard: ClipboardGuard | None = None,
    ) -> None:
        super().__init__(
            parent,
            title=tr("Password Generator"),
            subtitle=tr("Generate a strong unique password"),
            icon_name="key",
            width=480,
        )
        self._clipboard_guard = clipboard_guard
        self._anim: QPropertyAnimation | None = None

        self._preset_combo = QComboBox()
        self._preset_combo.setAccessibleName(tr("Password preset"))
        for preset in PRESETS:
            self._preset_combo.addItem(
                f"{preset.name} — {preset.description}", preset.name
            )
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        self._length = QSpinBox()
        self._length.setRange(4, 128)
        self._length.setValue(20)

        self._upper = QCheckBox(tr("Uppercase"))
        self._upper.setChecked(True)
        self._lower = QCheckBox(tr("Lowercase"))
        self._lower.setChecked(True)
        self._digits = QCheckBox(tr("Digits"))
        self._digits.setChecked(True)
        self._symbols = QCheckBox(tr("Symbols"))
        self._symbols.setChecked(True)
        self._ambiguous = QCheckBox(tr("Exclude ambiguous (O/0/Il1)"))
        self._ambiguous.setChecked(True)

        self._charset_row = QHBoxLayout()
        self._charset_chips: list[StatusChip] = []
        for key in ("A-Z", "a-z", "0-9", "#$"):
            chip = StatusChip(object_name="statusChip")
            chip.set_chip(key, "success")
            self._charset_chips.append(chip)
            self._charset_row.addWidget(chip)
        self._charset_row.addStretch(1)

        self._output = QLineEdit()
        self._output.setReadOnly(True)
        self._entropy_label = QLabel("")
        self._ring = CountdownRing(size=56)

        regenerate = QPushButton(tr("Generate"))
        regenerate.setProperty("cssClass", "secondary")
        regenerate.clicked.connect(self._regenerate)
        copy_btn = QPushButton(tr("Copy"))
        copy_btn.setProperty("cssClass", "secondary")
        copy_btn.clicked.connect(self._copy)

        out_row = QHBoxLayout()
        out_row.addWidget(self._output, stretch=1)
        out_row.addWidget(regenerate)
        out_row.addWidget(copy_btn)

        entropy_row = QHBoxLayout()
        entropy_row.addWidget(self._ring)
        entropy_row.addWidget(self._entropy_label, stretch=1)

        form = QFormLayout()
        form.addRow(tr("Preset"), self._preset_combo)
        form.addRow(tr("Length"), self._length)
        form.addRow("", self._upper)
        form.addRow("", self._lower)
        form.addRow("", self._digits)
        form.addRow("", self._symbols)
        form.addRow("", self._ambiguous)
        form.addRow(tr("Charset"), self._charset_row)
        form.addRow(tr("Password"), out_row)
        form.addRow(tr("Entropy"), entropy_row)
        self.body.addLayout(form)

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

        self.set_primary_text(tr("Use password"))
        self._regenerate()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self._anim = fade_in(self)

    def password(self) -> str:
        return self._output.text()

    def _on_preset_changed(self, index: int) -> None:
        if index < 0 or index >= len(PRESETS):
            return
        preset = PRESETS[index]
        opts = preset.options
        self._length.setValue(opts.length)
        self._upper.setChecked(opts.uppercase)
        self._lower.setChecked(opts.lowercase)
        self._digits.setChecked(opts.digits)
        self._symbols.setChecked(opts.symbols)
        self._ambiguous.setChecked(opts.exclude_ambiguous)

    def _options(self) -> GeneratorOptions:
        return GeneratorOptions(
            length=self._length.value(),
            uppercase=self._upper.isChecked(),
            lowercase=self._lower.isChecked(),
            digits=self._digits.isChecked(),
            symbols=self._symbols.isChecked(),
            exclude_ambiguous=self._ambiguous.isChecked(),
        )

    def _sync_charset_chips(self, opts: GeneratorOptions) -> None:
        flags = (opts.uppercase, opts.lowercase, opts.digits, opts.symbols)
        for chip, enabled in zip(self._charset_chips, flags, strict=True):
            chip.set_chip(chip.text() or "·", "success" if enabled else "muted")
            chip.setVisible(True)

    def _regenerate(self) -> None:
        try:
            opts = self._options()
            self._sync_charset_chips(opts)
            password = generate_password(opts)
            alphabet = build_alphabet(opts)
            bits = estimate_entropy_bits(password, len(alphabet))
            self._output.setText(password)
            self._entropy_label.setText(
                tr("~{bits:.0f} bits ({n} symbol alphabet)").format(
                    bits=bits, n=len(alphabet)
                )
            )
            self._ring.set_range(128)
            self._ring.set_value(min(128, int(bits)))
            self._ring.set_caption(f"{int(bits)}")
            if bits >= 80:
                self._ring.set_tone("success")
            elif bits >= 50:
                self._ring.set_tone("warning")
            else:
                self._ring.set_tone("danger")
        except ValueError as exc:
            self._output.clear()
            self._entropy_label.setText(str(exc))
            self._ring.set_value(0)
            self._ring.set_caption("")

    def _copy(self) -> None:
        if self._clipboard_guard is not None:
            self._clipboard_guard.copy(self._output.text())
