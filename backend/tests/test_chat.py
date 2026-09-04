import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.api.routes import chat


def make_llm(yield_chunks=None, side_effect=None):
    instance = MagicMock()

    def dummy_generator(**kwargs):
        if side_effect:
            raise side_effect
        yield from (yield_chunks or [])

    instance.stream_chat.side_effect = dummy_generator
    return MagicMock(return_value=instance), instance


def consume_stream(response: StreamingResponse) -> str:
    async def _consume():
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk)
        return "".join(chunks)

    return asyncio.run(_consume())


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
    chat_cache_mock.save_session.assert_called_once()


def test_session_not_found_returns_404():
    with patch("app.api.routes.chat.chat_cache") as chat_cache_mock:
        chat_cache_mock.get_session.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))
    assert exc_info.value.status_code == 404


def test_groq_success_used_and_gemini_never_called():
    groq_cls, _ = make_llm(yield_chunks=["Hi there, ", "from Groq"])
    gemini_cls, _ = make_llm()
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GroqProvider", groq_cls),
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))
        text = consume_stream(result)

    assert text == "Hi there, from Groq"
    gemini_cls.assert_not_called()


def test_groq_fails_falls_back_to_gemini():
    groq_cls, _ = make_llm(side_effect=RuntimeError("Groq is down"))
    gemini_cls, _ = make_llm(yield_chunks=["Hi from Gemini fallback"])
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GroqProvider", groq_cls),
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False
        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))
        text = consume_stream(result)

    assert text == "Hi from Gemini fallback"


def test_groq_fails_and_gemini_disabled_returns_error():
    groq_cls, _ = make_llm(side_effect=RuntimeError("Groq down"))
    gemini_cls, _ = make_llm()
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GroqProvider", groq_cls),
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = True
        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))
        text = consume_stream(result)

    assert text == "All LLM providers failed to generate a response."
    gemini_cls.assert_not_called()


def test_groq_fails_gemini_rate_limit_disables_gemini():
    groq_cls, _ = make_llm(side_effect=RuntimeError("Groq down"))
    gemini_cls, _ = make_llm(side_effect=RuntimeError("429 RESOURCE_EXHAUSTED"))
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GroqProvider", groq_cls),
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False
        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))
        text = consume_stream(result)

    assert text == "All LLM providers failed to generate a response."
    chat_cache_mock.disable_gemini.assert_called_once_with(ttl=300)


def test_both_providers_fail_returns_error_msg():
    groq_cls, _ = make_llm(side_effect=RuntimeError("groq down"))
    gemini_cls, _ = make_llm(side_effect=RuntimeError("gemini down too"))
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GroqProvider", groq_cls),
        patch("app.api.routes.chat.GeminiProvider", gemini_cls),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        chat_cache_mock.is_gemini_disabled.return_value = False
        result = chat.send_message(chat.ChatRequest(session_id="abc", message="hi"))
        text = consume_stream(result)

    assert text == "All LLM providers failed to generate a response."


def test_successful_response_gets_persisted_to_history():
    groq_cls, _ = make_llm(yield_chunks=["assistant ", "reply"])
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GroqProvider", groq_cls),
        patch("app.api.routes.chat.GeminiProvider"),
    ):
        chat_cache_mock.get_session.return_value = {"context": "ctx", "history": []}
        result = chat.send_message(
            chat.ChatRequest(session_id="abc", message="user question")
        )
        consume_stream(result)

    chat_cache_mock.append_messages.assert_called_once_with(
        session_id="abc",
        user_message="user question",
        assistant_message="assistant reply",
    )


def test_history_is_passed_through_to_provider():
    groq_cls, groq_instance = make_llm(yield_chunks=["reply"])
    with (
        patch("app.api.routes.chat.chat_cache") as chat_cache_mock,
        patch("app.api.routes.chat.GroqProvider", groq_cls),
        patch("app.api.routes.chat.GeminiProvider"),
    ):
        existing_history = [{"role": "user", "content": "earlier message"}]
        chat_cache_mock.get_session.return_value = {
            "context": "ctx",
            "history": existing_history,
        }
        result = chat.send_message(
            chat.ChatRequest(session_id="abc", message="follow up")
        )
        consume_stream(result)

    groq_instance.stream_chat.assert_called_once_with(
        context="ctx", history=existing_history, message="follow up"
    )
