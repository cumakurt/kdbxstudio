"""Tests for notes preview helpers."""

from kdbxstudio.ui.widgets.notes_preview import markdown_to_html, try_format_json


def test_markdown_headings_and_bold() -> None:
    html = markdown_to_html("# Title\n\n**bold** text")
    assert "<h1>Title</h1>" in html
    assert "<b>bold</b>" in html


def test_json_pretty() -> None:
    assert try_format_json('{"a":1}') == '{\n  "a": 1\n}'
    assert try_format_json("not json") is None
