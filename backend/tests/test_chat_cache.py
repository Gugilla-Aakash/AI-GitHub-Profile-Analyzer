import importlib
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

MODULE_PATH = "app.cache.chat_cache"


@pytest.fixture
def chat_cache_module():
    with (
        patch("redis.Redis.from_url") as mock_from_url,
        patch("app.config.settings") as mock_settings,
    ):
        mock_settings.REDIS_URL = "redis://fake:6379/0"
        mock_settings.CACHE_TTL = 300

        mock_redis_instance = MagicMock()
        mock_from_url.return_value = mock_redis_instance

        sys.modules.pop(MODULE_PATH, None)
        module = importlib.import_module(MODULE_PATH)

        yield module, mock_redis_instance, mock_settings

        sys.modules.pop(MODULE_PATH, None)


class TestInitAndKeying:
    def test_creates_redis_client_from_url(self, chat_cache_module):
        module, _, mock_settings = chat_cache_module

        with patch("redis.Redis.from_url") as mock_from_url:
            module.ChatCache()

            mock_from_url.assert_called_once_with(
                mock_settings.REDIS_URL,
                decode_responses=True,
            )

    def test_key_namespaces_session_id(self, chat_cache_module):
        module, _, _ = chat_cache_module
        cache = module.ChatCache()

        assert cache._key("session123") == "chat:session123"

    def test_key_strips_whitespace(self, chat_cache_module):
        module, _, _ = chat_cache_module
        cache = module.ChatCache()

        assert cache._key("  session123  ") == "chat:session123"


class TestSaveAndGetSession:
    def test_save_session_stores_json_payload_with_ttl(self, chat_cache_module):
        module, mock_redis, mock_settings = chat_cache_module
        cache = module.ChatCache()

        cache.save_session(
            session_id="s123",
            username="octocat",
            context="profile context",
            history=[{"role": "user", "content": "hi"}],
        )

        expected_payload = {
            "username": "octocat",
            "context": "profile context",
            "history": [{"role": "user", "content": "hi"}],
        }

        mock_redis.setex.assert_called_once_with(
            "chat:s123",
            mock_settings.CACHE_TTL,
            json.dumps(expected_payload),
        )

    def test_get_session_returns_none_when_missing(self, chat_cache_module):
        module, mock_redis, _ = chat_cache_module
        cache = module.ChatCache()
        mock_redis.get.return_value = None

        assert cache.get_session("s123") is None

    def test_get_session_returns_deserialized_data(self, chat_cache_module):
        module, mock_redis, _ = chat_cache_module
        cache = module.ChatCache()

        payload = {
            "username": "octocat",
            "context": "ctx",
            "history": [],
        }
        mock_redis.get.return_value = json.dumps(payload)

        result = cache.get_session("s123")
        assert result == payload

    def test_get_session_handles_invalid_json(self, chat_cache_module):
        module, mock_redis, _ = chat_cache_module
        cache = module.ChatCache()
        mock_redis.get.return_value = "invalid-json{"

        assert cache.get_session("s123") is None


class TestAppendMessages:
    def test_appends_turns_and_saves_updated_session(self, chat_cache_module):
        module, mock_redis, mock_settings = chat_cache_module
        cache = module.ChatCache()

        initial_session = {
            "username": "octocat",
            "context": "ctx",
            "history": [{"role": "user", "content": "hello"}],
        }
        mock_redis.get.return_value = json.dumps(initial_session)

        cache.append_messages(
            session_id="s123",
            user_message="what repos do I have?",
            assistant_message="You have repo1.",
        )

        expected_updated_session = {
            "username": "octocat",
            "context": "ctx",
            "history": [
                {"role": "user", "content": "hello"},
                {"role": "user", "content": "what repos do I have?"},
                {"role": "assistant", "content": "You have repo1."},
            ],
        }

        mock_redis.setex.assert_called_once_with(
            "chat:s123",
            mock_settings.CACHE_TTL,
            json.dumps(expected_updated_session),
        )

    def test_raises_value_error_if_session_not_found(self, chat_cache_module):
        module, mock_redis, _ = chat_cache_module
        cache = module.ChatCache()
        mock_redis.get.return_value = None

        with pytest.raises(ValueError, match="Chat session 's999' not found"):
            cache.append_messages("s999", "hi", "hello")


class TestGeminiDisableFlags:
    def test_is_gemini_disabled_returns_true_when_key_exists(self, chat_cache_module):
        module, mock_redis, _ = chat_cache_module
        cache = module.ChatCache()
        mock_redis.exists.return_value = 1

        assert cache.is_gemini_disabled() is True
        mock_redis.exists.assert_called_once_with("llm:gemini_disabled")

    def test_is_gemini_disabled_returns_false_when_key_missing(self, chat_cache_module):
        module, mock_redis, _ = chat_cache_module
        cache = module.ChatCache()
        mock_redis.exists.return_value = 0

        assert cache.is_gemini_disabled() is False

    def test_disable_gemini_sets_cooldown_key_with_ttl(self, chat_cache_module):
        module, mock_redis, _ = chat_cache_module
        cache = module.ChatCache()

        cache.disable_gemini(ttl=600)

        mock_redis.setex.assert_called_once_with(
            "llm:gemini_disabled",
            600,
            "1",
        )
