from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.routes import chat


def make_gemini(return_value=None, side_effect=None):
    instance = MagicMock()
    instance.chat.return_value = return_value
    if side_effect:
        instance.chat.side_effect = side_effect
    return MagicMock(return_value=instance), instance


# ---- start_chat tests ----


def test_profile_not_found_returns_404():
    with patch("app.api.routes.chat.cache") as cache_mock:
        cache_mock.get_profile.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            chat.start_chat("someuser")
    assert exc_info.value.status_code == 404


def test_username_normalized_before_cache_lookup():
    with (
        patch("app.api.routes.chat.cache") as cache_mock,
        patch("app.api.routes.chat.build_profile_context") as build_ctx,
        patch("app.api.routes.chat.chat_cache"),
    ):
        cache_mock.get_profile.return_value = {"grade": "A"}
        build_ctx.return_value = "some context"
        result = chat.start_chat("  SomeUser  ")
    cache_mock.get_profile.assert_called_once_with("someuser")
    assert result["username"] == "someuser"


def test_start_chat_saves_session_and_returns_session_id():
    with (
        patch("app.api.routes.chat.cache") as cache_mock,
        patch("app.api.routes.chat.build_profile_context") as build_ctx,
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
    ):
        cache_mock.get_profile.return_value = {"grade": "A"}
        build_ctx.return_value = "built context"

        result = chat.start_chat("someuser")

    assert "session_id" in result
    assert result["message"] == "Chat session initialized."
    chat_cache_mock.save_session.assert_called_once()
    call_kwargs = chat_cache_mock.save_session.call_args.kwargs
    assert call_kwargs["username"] == "someuser"
    assert call_kwargs["context"] == "built context"
    assert call_kwargs["history"] == []


# ---- send_message tests ----


def test_session_not_found_returns_404():
    with patch("app.api.routes.chat.chat_cache") as chat_cache_mock:
        chat_cache_mock.get_session.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))
    assert exc_info.value.status_code == 404


def test_gemini_success_used_and_groq_never_called():
    gemini_cls, _ = make_gemini(return_value="Hi there, from Gemini")
    groq_cls = MagicMock()
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
        patch("app.api.routes.chat.GroqProvider", groq_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False

        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))

    assert result["provider"] == "gemini"
    assert result["response"] == "Hi there, from Gemini"
    groq_cls.assert_not_called()


def test_gemini_disabled_skips_straight_to_groq():
    gemini_cls = MagicMock()
    groq_cls, _ = make_gemini(return_value="Hi from Groq")
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
        patch("app.api.routes.chat.GroqProvider", groq_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = True

        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))

    assert result["provider"] == "groq"
    gemini_cls.assert_not_called()


def test_gemini_rate_limit_error_disables_gemini_for_24h_and_falls_back():
    gemini_cls, _ = make_gemini(side_effect=RuntimeError("429 RESOURCE_EXHAUSTED"))
    groq_cls, _ = make_gemini(return_value="fallback response")
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
        patch("app.api.routes.chat.GroqProvider", groq_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False

        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))

    assert result["provider"] == "groq"
    chat_cache_mock.disable_gemini.assert_called_once_with(ttl=86400)


def test_gemini_generic_error_falls_back_without_disabling():
    gemini_cls, _ = make_gemini(side_effect=RuntimeError("connection reset"))
    groq_cls, _ = make_gemini(return_value="fallback response")
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
        patch("app.api.routes.chat.GroqProvider", groq_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False

        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))

    assert result["provider"] == "groq"
    chat_cache_mock.disable_gemini.assert_not_called()


def test_gemini_empty_response_falls_back_to_groq():
    # this is the bug we fixed, gemini succeeding but handing back nothing
    gemini_cls, _ = make_gemini(return_value="")
    groq_cls, _ = make_gemini(return_value="real answer from groq")
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
        patch("app.api.routes.chat.GroqProvider", groq_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False

        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))

    assert result["provider"] == "groq"
    assert result["response"] == "real answer from groq"


def test_gemini_whitespace_only_response_falls_back_to_groq():
    gemini_cls, _ = make_gemini(return_value="   \n  ")
    groq_cls, _ = make_gemini(return_value="real answer")
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
        patch("app.api.routes.chat.GroqProvider", groq_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False

        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))

    assert result["provider"] == "groq"


def test_both_providers_fail_returns_502():
    gemini_cls, _ = make_gemini(side_effect=RuntimeError("gemini down"))
    groq_cls, _ = make_gemini(side_effect=RuntimeError("groq down too"))
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
        patch("app.api.routes.chat.GroqProvider", groq_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))

    assert exc_info.value.status_code == 502


def test_successful_response_gets_persisted_to_history():
    gemini_cls, _ = make_gemini(return_value="assistant reply")
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
        patch("app.api.routes.chat.GroqProvider"),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False

        chat.send_message(chat.ChatRequest(session_id="abc", message="user question"))

    chat_cache_mock.append_messages.assert_called_once_with(
        session_id="abc",
        user_message="user question",
        assistant_message="assistant reply",
    )


def test_history_is_passed_through_to_provider():
    gemini_cls, gemini_instance = make_gemini(return_value="reply")
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
        patch("app.api.routes.chat.GroqProvider"),
    ):
        existing_history = [{"role": "user", "content": "earlier message"}]
        chat_cache_mock.get_session.return_value = {
            "context": "ctx",
            "history": existing_history,
        }
        chat_cache_mock.is_gemini_disabled.return_value = False

        chat.send_message(chat.ChatRequest(session_id="abc", message="follow up"))

    gemini_instance.chat.assert_called_once_with(
        context="ctx", history=existing_history, message="follow up"
    )
