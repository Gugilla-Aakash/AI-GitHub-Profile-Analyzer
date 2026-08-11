from unittest.mock import MagicMock, patch

from app.reports import markdown_report


def make_gemini(return_value=None, side_effect=None):
    mock_instance = MagicMock()
    mock_instance.chat.return_value = return_value
    if side_effect:
        mock_instance.chat.side_effect = side_effect
    mock_cls = MagicMock(return_value=mock_instance)
    return mock_cls, mock_instance


def test_insufficient_data_skips_llm_entirely():
    with (
        patch("app.reports.markdown_report.GeminiProvider") as gemini,
        patch("app.reports.markdown_report.GroqProvider") as groq,
    ):
        result = markdown_report.generate_markdown_report(
            {"insufficient_data": True, "username": "octocat"}
        )
    assert "octocat" in result
    assert "Insufficient public data" in result
    gemini.assert_not_called()
    groq.assert_not_called()


def test_gemini_success_returns_its_text_and_groq_not_touched():
    gemini_cls, _ = make_gemini(return_value="# Great Report\nlots of content here")
    groq_cls = MagicMock()
    with (
        patch("app.reports.markdown_report.GeminiProvider", gemini_cls),
        patch("app.reports.markdown_report.GroqProvider", groq_cls),
    ):
        result = markdown_report._generate_full_report("some profile context")
    assert result == "# Great Report\nlots of content here"
    groq_cls.assert_not_called()


def test_gemini_raises_falls_back_to_groq():
    gemini_cls, _ = make_gemini(side_effect=RuntimeError("gemini is down"))
    groq_cls, _ = make_gemini(return_value="# Groq Report\nbackup content")
    with (
        patch("app.reports.markdown_report.GeminiProvider", gemini_cls),
        patch("app.reports.markdown_report.GroqProvider", groq_cls),
    ):
        result = markdown_report._generate_full_report("some profile context")
    assert result == "# Groq Report\nbackup content"


def test_gemini_returns_empty_string_falls_back_to_groq():
    # this is the actual bug we fixed, gemini not raising but giving nothing back
    gemini_cls, _ = make_gemini(return_value="")
    groq_cls, groq_instance = make_gemini(return_value="# Groq Saved The Day")
    with (
        patch("app.reports.markdown_report.GeminiProvider", gemini_cls),
        patch("app.reports.markdown_report.GroqProvider", groq_cls),
    ):
        result = markdown_report._generate_full_report("some profile context")
    assert result == "# Groq Saved The Day"
    groq_instance.chat.assert_called_once()


def test_gemini_returns_whitespace_only_falls_back_to_groq():
    gemini_cls, _ = make_gemini(return_value="   \n\n   ")
    groq_cls, _ = make_gemini(return_value="# Real Content From Groq")
    with (
        patch("app.reports.markdown_report.GeminiProvider", gemini_cls),
        patch("app.reports.markdown_report.GroqProvider", groq_cls),
    ):
        result = markdown_report._generate_full_report("some profile context")
    assert result == "# Real Content From Groq"


def test_gemini_returns_none_falls_back_to_groq():
    gemini_cls, _ = make_gemini(return_value=None)
    groq_cls, _ = make_gemini(return_value="# From Groq")
    with (
        patch("app.reports.markdown_report.GeminiProvider", gemini_cls),
        patch("app.reports.markdown_report.GroqProvider", groq_cls),
    ):
        result = markdown_report._generate_full_report("some profile context")
    assert result == "# From Groq"


def test_both_providers_raise_returns_fallback_message():
    gemini_cls, _ = make_gemini(side_effect=RuntimeError("gemini down"))
    groq_cls, _ = make_gemini(side_effect=RuntimeError("groq down too"))
    with (
        patch("app.reports.markdown_report.GeminiProvider", gemini_cls),
        patch("app.reports.markdown_report.GroqProvider", groq_cls),
    ):
        result = markdown_report._generate_full_report("some profile context")
    assert "Unable to synthesize" in result


def test_both_providers_return_empty_returns_fallback_message():
    gemini_cls, _ = make_gemini(return_value="")
    groq_cls, _ = make_gemini(return_value="")
    with (
        patch("app.reports.markdown_report.GeminiProvider", gemini_cls),
        patch("app.reports.markdown_report.GroqProvider", groq_cls),
    ):
        result = markdown_report._generate_full_report("some profile context")
    assert "Unable to synthesize" in result


def test_gemini_raises_and_groq_returns_empty_gives_fallback_message():
    gemini_cls, _ = make_gemini(side_effect=RuntimeError("gemini down"))
    groq_cls, _ = make_gemini(return_value="")
    with (
        patch("app.reports.markdown_report.GeminiProvider", gemini_cls),
        patch("app.reports.markdown_report.GroqProvider", groq_cls),
    ):
        result = markdown_report._generate_full_report("some profile context")
    assert "Unable to synthesize" in result


def test_generate_markdown_report_builds_context_and_calls_llm():
    with (
        patch("app.reports.markdown_report.build_profile_context") as build_ctx,
        patch("app.reports.markdown_report._generate_full_report") as gen_report,
    ):
        build_ctx.return_value = "built context string"
        gen_report.return_value = "final markdown"
        result = markdown_report.generate_markdown_report({"username": "someone"})
    build_ctx.assert_called_once_with({"username": "someone"})
    gen_report.assert_called_once_with("built context string")
    assert result == "final markdown"


def test_result_gets_stripped_of_surrounding_whitespace():
    gemini_cls, _ = make_gemini(return_value="   \n# Report With Padding\n\n   ")
    groq_cls = MagicMock()
    with (
        patch("app.reports.markdown_report.GeminiProvider", gemini_cls),
        patch("app.reports.markdown_report.GroqProvider", groq_cls),
    ):
        result = markdown_report._generate_full_report("context")
    assert result == "# Report With Padding"
