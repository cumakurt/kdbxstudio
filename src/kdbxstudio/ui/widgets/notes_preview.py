"""Notes preview: Markdown render + JSON pretty-print."""

from __future__ import annotations

import json
import re
from html import escape

from PySide6.QtWidgets import (
    QLabel,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

_MD_HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
_MD_BOLD = re.compile(r"\*\*(.+?)\*\*")
_MD_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_MD_CODE = re.compile(r"`([^`]+)`")
_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_MD_UL = re.compile(r"^\s*[-*]\s+(.*)$", re.MULTILINE)


def markdown_to_html(text: str) -> str:
    """Minimal Markdown → HTML converter (no external dependency)."""
    if not text.strip():
        return "<p><i>No notes</i></p>"

    html = escape(text)
    html = _MD_CODE.sub(r"<code>\1</code>", html)
    html = _MD_BOLD.sub(r"<b>\1</b>", html)
    html = _MD_ITALIC.sub(r"<i>\1</i>", html)
    html = _MD_LINK.sub(r'<a href="\2">\1</a>', html)

    def heading_sub(match: re.Match[str]) -> str:
        level = len(match.group(1))
        return f"<h{level}>{match.group(2)}</h{level}>"

    html = _MD_HEADING.sub(heading_sub, html)
    html = _MD_UL.sub(r"<li>\1</li>", html)
    html = html.replace("\n\n", "</p><p>")
    html = html.replace("\n", "<br>")
    return f"<p>{html}</p>"


def try_format_json(text: str) -> str | None:
    """Return pretty JSON if `text` parses as JSON object/array."""
    stripped = text.strip()
    if not stripped or stripped[0] not in "{[":
        return None
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return json.dumps(data, indent=2, ensure_ascii=False)


class NotesPreviewWidget(QWidget):
    """Edit notes with Markdown and optional JSON previews."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = QTextEdit()
        self._md_preview = QTextBrowser()
        self._md_preview.setOpenExternalLinks(True)
        self._json_preview = QTextBrowser()
        self._json_status = QLabel("")

        preview_tabs = QTabWidget()
        md_page = QWidget()
        md_layout = QVBoxLayout(md_page)
        md_layout.setContentsMargins(0, 0, 0, 0)
        md_layout.addWidget(self._md_preview)

        json_page = QWidget()
        json_layout = QVBoxLayout(json_page)
        json_layout.setContentsMargins(0, 0, 0, 0)
        json_layout.addWidget(self._json_status)
        json_layout.addWidget(self._json_preview)

        preview_tabs.addTab(md_page, "Markdown")
        preview_tabs.addTab(json_page, "JSON")

        tabs = QTabWidget()
        tabs.addTab(self._editor, "Edit")
        tabs.addTab(preview_tabs, "Preview")
        tabs.currentChanged.connect(self._on_tab_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)
        self._tabs = tabs
        self._preview_tabs = preview_tabs

    def setPlainText(self, text: str) -> None:  # noqa: N802
        self._editor.setPlainText(text)
        self._refresh_previews()

    def toPlainText(self) -> str:  # noqa: N802
        return self._editor.toPlainText()

    def clear(self) -> None:
        self._editor.clear()
        self._md_preview.clear()
        self._json_preview.clear()
        self._json_status.clear()

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802
        super().setEnabled(enabled)
        self._editor.setEnabled(enabled)

    def _on_tab_changed(self, index: int) -> None:
        if index == 1:
            self._refresh_previews()

    def _refresh_previews(self) -> None:
        text = self._editor.toPlainText()
        self._md_preview.setHtml(markdown_to_html(text))
        formatted = try_format_json(text)
        if formatted is None:
            self._json_status.setText("Notes are not valid JSON.")
            self._json_preview.setPlainText(text)
        else:
            self._json_status.setText("Valid JSON")
            self._json_preview.setPlainText(formatted)
