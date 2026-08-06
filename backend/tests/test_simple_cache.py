import importlib
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

MODULE_PATH = "app.cache.simple_cache"


@pytest.fixture
def cache_module():
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


class TestInit:
    def test_creates_redis_client_from_url(self, cache_module):
        module, _, mock_settings = cache_module

        with patch("redis.Redis.from_url") as mock_from_url:
            module.SimpleCache()

            mock_from_url.assert_called_once_with(
                mock_settings.REDIS_URL,
                decode_responses=True,
            )


class TestGetKey:
    def test_lowercases_and_strips_username(self, cache_module):
        module, _, _ = cache_module
        cache = module.SimpleCache()

        assert cache._get_key("  UserName  ") == "profile:username"

    def test_namespaces_key(self, cache_module):
        module, _, _ = cache_module
        cache = module.SimpleCache()

        assert cache._get_key("octocat") == "profile:octocat"


class TestSetProfile:
    def test_serializes_and_stores_with_ttl(self, cache_module):
        module, mock_redis_instance, mock_settings = cache_module
        cache = module.SimpleCache()

        data = {"username": "octocat", "repos": 8}
        cache.set_profile("octocat", data)

        mock_redis_instance.setex.assert_called_once_with(
            name="profile:octocat",
            time=mock_settings.CACHE_TTL,
            value=json.dumps(data),
        )

    def test_key_is_normalized(self, cache_module):
        module, mock_redis_instance, _ = cache_module
        cache = module.SimpleCache()

        cache.set_profile("  OctoCat  ", {"foo": "bar"})

        _, kwargs = mock_redis_instance.setex.call_args
        assert kwargs["name"] == "profile:octocat"


class TestGetProfile:
    def test_returns_none_when_key_missing(self, cache_module):
        module, mock_redis_instance, _ = cache_module
        cache = module.SimpleCache()
        mock_redis_instance.get.return_value = None

        result = cache.get_profile("octocat")

        assert result is None

    def test_returns_deserialized_data(self, cache_module):
        module, mock_redis_instance, _ = cache_module
        cache = module.SimpleCache()
        data = {"username": "octocat", "repos": 8}
        mock_redis_instance.get.return_value = json.dumps(data)

        result = cache.get_profile("octocat")

        assert result == data

    def test_uses_normalized_key_for_lookup(self, cache_module):
        module, mock_redis_instance, _ = cache_module
        cache = module.SimpleCache()
        mock_redis_instance.get.return_value = None

        cache.get_profile("  OctoCat  ")

        mock_redis_instance.get.assert_called_once_with("profile:octocat")

    def test_returns_none_on_invalid_json(self, cache_module, caplog):
        module, mock_redis_instance, _ = cache_module
        cache = module.SimpleCache()
        mock_redis_instance.get.return_value = "not-valid-json"

        result = cache.get_profile("octocat")

        assert result is None
        assert "Failed to decode cached profile" in caplog.text

    def test_returns_none_on_type_error(self, cache_module):
        module, mock_redis_instance, _ = cache_module
        cache = module.SimpleCache()
        # json.loads() raises TypeError if it gets a non-str/bytes value
        mock_redis_instance.get.return_value = 12345

        result = cache.get_profile("octocat")

        assert result is None


class TestSingleton:
    def test_module_exposes_cache_instance(self, cache_module):
        module, _, _ = cache_module

        assert isinstance(module.cache, module.SimpleCache)
