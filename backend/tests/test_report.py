from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.api.routes import report


def test_profile_not_in_cache_returns_404():
    with (
        patch("app.api.routes.report.cache") as cache_mock,
        patch("app.api.routes.report.generate_markdown_report") as gen_mock,
    ):
        cache_mock.get_profile.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            report.get_report("someuser")
    assert exc_info.value.status_code == 404
    assert "someuser" in exc_info.value.detail
    gen_mock.assert_not_called()


def test_username_lowercased_for_cache_lookup():
    with (
        patch("app.api.routes.report.cache") as cache_mock,
        patch("app.api.routes.report.generate_markdown_report"),
    ):
        cache_mock.get_profile.return_value = None
        with pytest.raises(HTTPException):
            report.get_report("SomeUser")
    cache_mock.get_profile.assert_called_once_with("someuser")


def test_default_format_returns_markdown_response():
    with (
        patch("app.api.routes.report.cache") as cache_mock,
        patch("app.api.routes.report.generate_markdown_report") as gen_mock,
    ):
        cache_mock.get_profile.return_value = {"grade": "A"}
        gen_mock.return_value = "# Report Content"

        response = report.get_report("someuser")

    assert response.media_type == "text/markdown; charset=utf-8"
    assert response.body == b"# Report Content"
    assert (
        'inline; filename="someuser_github_audit.md"'
        in response.headers["content-disposition"]
    )


def test_pdf_format_returns_pdf_response():
    with (
        patch("app.api.routes.report.cache") as cache_mock,
        patch("app.api.routes.report.generate_markdown_report") as gen_mock,
        patch("app.api.routes.report.convert_markdown_to_pdf") as pdf_mock,
    ):
        cache_mock.get_profile.return_value = {"grade": "A"}
        gen_mock.return_value = "# Report Content"
        pdf_mock.return_value = b"%PDF-fake-bytes"

        response = report.get_report("someuser", format="pdf")

    assert response.media_type == "application/pdf"
    assert response.body == b"%PDF-fake-bytes"
    assert (
        'attachment; filename="someuser_github_audit.pdf"'
        in response.headers["content-disposition"]
    )


def test_pdf_generation_failure_returns_500_with_generic_message():
    with (
        patch("app.api.routes.report.cache") as cache_mock,
        patch("app.api.routes.report.generate_markdown_report") as gen_mock,
        patch("app.api.routes.report.convert_markdown_to_pdf") as pdf_mock,
    ):
        cache_mock.get_profile.return_value = {"grade": "A"}
        gen_mock.return_value = "# Report Content"
        pdf_mock.side_effect = RuntimeError(
            "weasyprint blew up with some internal path leak"
        )

        with pytest.raises(HTTPException) as exc_info:
            report.get_report("someuser", format="pdf")

    assert exc_info.value.status_code == 500
    # the raw internal error text should not leak into the client facing detail
    assert "weasyprint" not in exc_info.value.detail
    assert "internal path leak" not in exc_info.value.detail


def test_markdown_format_never_calls_pdf_converter():
    with (
        patch("app.api.routes.report.cache") as cache_mock,
        patch("app.api.routes.report.generate_markdown_report") as gen_mock,
        patch("app.api.routes.report.convert_markdown_to_pdf") as pdf_mock,
    ):
        cache_mock.get_profile.return_value = {"grade": "A"}
        gen_mock.return_value = "# Report Content"

        report.get_report("someuser", format="md")

    pdf_mock.assert_not_called()


def test_cache_control_header_present_on_both_formats():
    with (
        patch("app.api.routes.report.cache") as cache_mock,
        patch("app.api.routes.report.generate_markdown_report") as gen_mock,
        patch("app.api.routes.report.convert_markdown_to_pdf") as pdf_mock,
    ):
        cache_mock.get_profile.return_value = {"grade": "A"}
        gen_mock.return_value = "# Report Content"
        pdf_mock.return_value = b"%PDF-bytes"

        md_response = report.get_report("someuser", format="md")
        pdf_response = report.get_report("someuser", format="pdf")

    assert md_response.headers["cache-control"] == "no-store"
    assert pdf_response.headers["cache-control"] == "no-store"
