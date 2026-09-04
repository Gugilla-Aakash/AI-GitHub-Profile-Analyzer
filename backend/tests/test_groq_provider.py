from unittest.mock import MagicMock, patch

import pytest

import app.clients.llm.groq_provider as groq_provider_module
from app.clients.llm.groq_provider import GroqProvider


@pytest.fixture(autouse=True)
def reset_singleton():
    groq_provider_module._groq_client = None
    yield
    groq_provider_module._groq_client = None


@pytest.fixture
def mock_settings():
    with patch("app.clients.llm.groq_provider.settings") as settings:
        settings.GROQ_API_KEY = "fake-api-key"
        yield settings


@pytest.fixture
def mock_groq_client():
    with patch("app.clients.llm.groq_provider.Groq") as client_cls:
        client_instance = MagicMock()
        client_cls.return_value = client_instance
        yield client_cls, client_instance


def mock_response(text):
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    res = MagicMock()
    res.choices = [choice]
    return res


class TestInit:
    def test_raises_if_api_key_missing(self, mock_settings):
        mock_settings.GROQ_API_KEY = ""
        with pytest.raises(ValueError, match="GROQ_API_KEY is not provided"):
            GroqProvider()

    def test_creates_client_with_api_key(self, mock_settings, mock_groq_client):
        client_cls, _ = mock_groq_client
        provider = GroqProvider()
        client_cls.assert_called_once_with(api_key="fake-api-key")
        assert provider.model == "openai/gpt-oss-20b"


class TestChat:
    def _make_provider(self, mock_settings, mock_groq_client):
        return GroqProvider()

    def test_returns_stripped_response_text(self, mock_settings, mock_groq_client):
        _, client_instance = mock_groq_client
        client_instance.chat.completions.create.return_value = mock_response(
            "  hey there!  "
        )
        provider = self._make_provider(mock_settings, mock_groq_client)
        result = provider.chat(context="some context", history=[], message="hi")
        assert result == "hey there!"

    def test_returns_empty_string_when_content_is_none(
        self, mock_settings, mock_groq_client
    ):
        _, client_instance = mock_groq_client
        client_instance.chat.completions.create.return_value = mock_response(None)
        provider = self._make_provider(mock_settings, mock_groq_client)
        result = provider.chat(context="ctx", history=[], message="hi")
        assert result == ""

    def test_calls_create_with_correct_model_and_temperature(
        self, mock_settings, mock_groq_client
    ):
        _, client_instance = mock_groq_client
        client_instance.chat.completions.create.return_value = mock_response("ok")
        provider = self._make_provider(mock_settings, mock_groq_client)
        provider.chat(context="ctx", history=[], message="hi")
        _, kwargs = client_instance.chat.completions.create.call_args
        assert kwargs["model"] == "openai/gpt-oss-20b"
        assert kwargs["temperature"] == 0.2

    def test_system_prompt_includes_context(self, mock_settings, mock_groq_client):
        _, client_instance = mock_groq_client
        client_instance.chat.completions.create.return_value = mock_response("ok")
        provider = self._make_provider(mock_settings, mock_groq_client)
        provider.chat(context="Repo: my-cool-project", history=[], message="hi")
        _, kwargs = client_instance.chat.completions.create.call_args
        assert kwargs["messages"][0]["role"] == "system"
        assert "Repo: my-cool-project" in kwargs["messages"][0]["content"]

    def test_history_roles_preserved(self, mock_settings, mock_groq_client):
        _, client_instance = mock_groq_client
        client_instance.chat.completions.create.return_value = mock_response("ok")
        history = [
            {"role": "user", "content": "what languages do you use?"},
            {"role": "assistant", "content": "mostly python and typescript"},
        ]
        provider = self._make_provider(mock_settings, mock_groq_client)
        provider.chat(context="ctx", history=history, message="cool, anything else?")
        _, kwargs = client_instance.chat.completions.create.call_args
        assert len(kwargs["messages"]) == 4

    def test_current_message_appended_last(self, mock_settings, mock_groq_client):
        _, client_instance = mock_groq_client
        client_instance.chat.completions.create.return_value = mock_response("ok")
        provider = self._make_provider(mock_settings, mock_groq_client)
        provider.chat(
            context="ctx",
            history=[{"role": "user", "content": "first"}],
            message="latest message",
        )
        _, kwargs = client_instance.chat.completions.create.call_args
        assert kwargs["messages"][-1]["content"] == "latest message"

    def test_skips_history_entries_with_invalid_role(
        self, mock_settings, mock_groq_client
    ):
        _, client_instance = mock_groq_client
        client_instance.chat.completions.create.return_value = mock_response("ok")
        history = [
            {"role": "system", "content": "skip"},
            {"role": "assistant", "content": "real"},
        ]
        provider = self._make_provider(mock_settings, mock_groq_client)
        provider.chat(context="ctx", history=history, message="new")
        _, kwargs = client_instance.chat.completions.create.call_args
        assert len(kwargs["messages"]) == 3

    def test_skips_history_entries_with_empty_content(
        self, mock_settings, mock_groq_client
    ):
        _, client_instance = mock_groq_client
        client_instance.chat.completions.create.return_value = mock_response("ok")
        history = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "real"},
        ]
        provider = self._make_provider(mock_settings, mock_groq_client)
        provider.chat(context="ctx", history=history, message="new")
        _, kwargs = client_instance.chat.completions.create.call_args
        assert len(kwargs["messages"]) == 3
