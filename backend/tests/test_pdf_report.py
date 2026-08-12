from unittest.mock import patch

import pytest

from app.reports import pdf_report
from app.reports.pdf_report import convert_markdown_to_pdf


def test_returns_bytes_on_success():
    with patch("app.reports.pdf_report.HTML") as html_cls:
        html_cls.return_value.write_pdf.return_value = b"%PDF-fake-bytes"
        result = convert_markdown_to_pdf("# Hello World")
    assert result == b"%PDF-fake-bytes"


def test_raises_runtime_error_when_write_pdf_returns_none():
    with patch("app.reports.pdf_report.HTML") as html_cls:
        html_cls.return_value.write_pdf.return_value = None
        with pytest.raises(RuntimeError, match="PDF generation failed"):
            convert_markdown_to_pdf("# Hello World")


def test_markdown_headers_get_converted_to_html():
    with patch("app.reports.pdf_report.HTML") as html_cls:
        html_cls.return_value.write_pdf.return_value = b"pdf-bytes"
        convert_markdown_to_pdf("# Big Title\n## Smaller Title")
    passed_html = html_cls.call_args.kwargs["string"]
    assert "<h1>Big Title</h1>" in passed_html
    assert "<h2>Smaller Title</h2>" in passed_html


def test_markdown_tables_get_converted():
    md = "| A | B |\n| --- | --- |\n| 1 | 2 |"
    with patch("app.reports.pdf_report.HTML") as html_cls:
        html_cls.return_value.write_pdf.return_value = b"pdf-bytes"
        convert_markdown_to_pdf(md)
    passed_html = html_cls.call_args.kwargs["string"]
    assert "<table>" in passed_html
    assert "<th>A</th>" in passed_html


def test_fenced_code_blocks_get_converted():
    md = "```\nprint('hi')\n```"
    with patch("app.reports.pdf_report.HTML") as html_cls:
        html_cls.return_value.write_pdf.return_value = b"pdf-bytes"
        convert_markdown_to_pdf(md)
    passed_html = html_cls.call_args.kwargs["string"]
    assert "<pre>" in passed_html
    assert "<code>" in passed_html


def test_single_newlines_become_line_breaks():
    # nl2br extension, plain paragraph with a single newline should turn into <br>
    md = "line one\nline two"
    with patch("app.reports.pdf_report.HTML") as html_cls:
        html_cls.return_value.write_pdf.return_value = b"pdf-bytes"
        convert_markdown_to_pdf(md)
    passed_html = html_cls.call_args.kwargs["string"]
    assert "<br" in passed_html


def test_styles_are_embedded_in_output_html():
    with patch("app.reports.pdf_report.HTML") as html_cls:
        html_cls.return_value.write_pdf.return_value = b"pdf-bytes"
        convert_markdown_to_pdf("some content")
    passed_html = html_cls.call_args.kwargs["string"]
    assert pdf_report.PREMIUM_PDF_STYLES in passed_html
    assert "<style>" in passed_html


def test_empty_markdown_still_produces_valid_html_shell():
    with patch("app.reports.pdf_report.HTML") as html_cls:
        html_cls.return_value.write_pdf.return_value = b"pdf-bytes"
        convert_markdown_to_pdf("")
    passed_html = html_cls.call_args.kwargs["string"]
    assert "<!DOCTYPE html>" in passed_html
    assert "<body>" in passed_html


def test_html_is_utf8_declared():
    with patch("app.reports.pdf_report.HTML") as html_cls:
        html_cls.return_value.write_pdf.return_value = b"pdf-bytes"
        convert_markdown_to_pdf("some content with emoji 🚀")
    passed_html = html_cls.call_args.kwargs["string"]
    assert 'charset="utf-8"' in passed_html
