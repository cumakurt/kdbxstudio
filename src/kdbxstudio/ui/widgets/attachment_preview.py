"""Attachment list + PDF / binary preview."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kdbxstudio.core.database import AttachmentView
from kdbxstudio.i18n import tr


class AttachmentPreviewWidget(QWidget):
    """Lists entry attachments and previews PDF or text payloads."""

    add_requested = Signal()
    delete_requested = Signal(int)
    files_dropped = Signal(list)
    save_requested = Signal(int, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._attachments: list[AttachmentView] = []
        self._pdf_buffer: QBuffer | None = None
        self.setAcceptDrops(True)

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_row)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_list_menu)

        self._info = QLabel(tr("No attachment selected"))
        self._info.setWordWrap(True)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._pdf_doc = QPdfDocument(self)
        self._pdf_view = QPdfView()
        self._pdf_view.setDocument(self._pdf_doc)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._text)
        self._stack.addWidget(self._pdf_view)

        add_btn = QPushButton(tr("Add…"))
        add_btn.clicked.connect(self.add_requested.emit)
        del_btn = QPushButton(tr("Remove"))
        del_btn.clicked.connect(self._emit_delete)
        save_btn = QPushButton(tr("Save as…"))
        save_btn.clicked.connect(self._emit_save)

        buttons = QHBoxLayout()
        buttons.addWidget(add_btn)
        buttons.addWidget(del_btn)
        buttons.addWidget(save_btn)
        buttons.addStretch()

        left = QVBoxLayout()
        left.addWidget(QLabel(tr("Attachments (drop files here)")))
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
        self._info.setText(tr("No attachment selected"))
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
            self._info.setText(tr("No attachment selected"))
            self._text.clear()
            self._close_pdf()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: list[str] = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local:
                paths.append(local)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()

    def _close_pdf(self) -> None:
        self._pdf_doc.close()
        if self._pdf_buffer is not None:
            self._pdf_buffer.close()
            self._pdf_buffer = None

    def _emit_delete(self) -> None:
        row = self._list.currentRow()
        if 0 <= row < len(self._attachments):
            self.delete_requested.emit(self._attachments[row].id)

    def _show_list_menu(self, pos) -> None:
        item = self._list.itemAt(pos)
        if item is not None:
            self._list.setCurrentItem(item)
        row = self._list.currentRow()
        has_item = 0 <= row < len(self._attachments)
        menu = QMenu(self)
        menu.addAction(tr("Add…"), self.add_requested.emit)
        remove = menu.addAction(tr("Remove"), self._emit_delete)
        save = menu.addAction(tr("Save as…"), self._emit_save)
        remove.setEnabled(has_item)
        save.setEnabled(has_item)
        menu.exec(self._list.mapToGlobal(pos))

    def _emit_save(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._attachments):
            return
        item = self._attachments[row]
        safe_name = Path(item.filename).name or "attachment"
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Save attachment"), safe_name
        )
        if not path:
            return
        try:
            Path(path).write_bytes(item.data)
        except OSError as exc:
            QMessageBox.critical(self, tr("Save failed"), str(exc))
            return
        self.save_requested.emit(item.id, path)

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
            text = tr("Binary attachment (hex preview):\n") + preview.hex(" ")
        self._text.setPlainText(text)
        self._stack.setCurrentWidget(self._text)
