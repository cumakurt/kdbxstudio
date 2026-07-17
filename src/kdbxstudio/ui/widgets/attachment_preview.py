"""Attachment list + PDF / binary preview."""

from __future__ import annotations

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Signal
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.core.database import AttachmentView


class AttachmentPreviewWidget(QWidget):
    """Lists entry attachments and previews PDF or text payloads."""

    add_requested = Signal()
    delete_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._attachments: list[AttachmentView] = []
        self._pdf_buffer: QBuffer | None = None

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_row)

        self._info = QLabel("No attachment selected")
        self._info.setWordWrap(True)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._pdf_doc = QPdfDocument(self)
        self._pdf_view = QPdfView()
        self._pdf_view.setDocument(self._pdf_doc)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._text)
        self._stack.addWidget(self._pdf_view)

        add_btn = QPushButton("Add…")
        add_btn.clicked.connect(self.add_requested.emit)
        del_btn = QPushButton("Remove")
        del_btn.clicked.connect(self._emit_delete)

        buttons = QHBoxLayout()
        buttons.addWidget(add_btn)
        buttons.addWidget(del_btn)
        buttons.addStretch()

        left = QVBoxLayout()
        left.addWidget(QLabel("Attachments"))
        left.addWidget(self._list)
        left.addLayout(buttons)

        right = QVBoxLayout()
        right.addWidget(self._info)
        right.addWidget(self._stack)

        layout = QHBoxLayout(self)
        layout.addLayout(left, 1)
        layout.addLayout(right, 2)

    def clear(self) -> None:
        self._attachments = []
        self._list.clear()
        self._info.setText("No attachment selected")
        self._text.clear()
        self._close_pdf()

    def set_attachments(self, attachments: list[AttachmentView]) -> None:
        self._attachments = attachments
        self._list.clear()
        for item in attachments:
            self._list.addItem(
                QListWidgetItem(f"{item.filename} ({item.size} bytes)")
            )
        if attachments:
            self._list.setCurrentRow(0)
        else:
            self._info.setText("No attachment selected")
            self._text.clear()
            self._close_pdf()

    def _close_pdf(self) -> None:
        self._pdf_doc.close()
        if self._pdf_buffer is not None:
            self._pdf_buffer.close()
            self._pdf_buffer = None

    def _emit_delete(self) -> None:
        row = self._list.currentRow()
        if 0 <= row < len(self._attachments):
            self.delete_requested.emit(self._attachments[row].id)

    def _on_row(self, row: int) -> None:
        if row < 0 or row >= len(self._attachments):
            return
        item = self._attachments[row]
        self._info.setText(f"{item.filename} — {item.size} bytes")
        name = item.filename.lower()
        if name.endswith(".pdf"):
            self._close_pdf()
            self._pdf_buffer = QBuffer()
            self._pdf_buffer.setData(QByteArray(item.data))
            self._pdf_buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            self._pdf_doc.load(self._pdf_buffer)
            self._stack.setCurrentWidget(self._pdf_view)
            return
        self._close_pdf()
        try:
            text = item.data.decode("utf-8")
        except UnicodeDecodeError:
            preview = item.data[:512]
            text = "Binary attachment (hex preview):\n" + preview.hex(" ")
        self._text.setPlainText(text)
        self._stack.setCurrentWidget(self._text)
