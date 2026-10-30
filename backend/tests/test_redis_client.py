from unittest.mock import MagicMock, patch

import pytest
import redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.cache.memory_store import InMemoryRedis
from app.cache import redis_client as rc


@pytest.fixture(autouse=True)
def _reset_client():
    rc.reset_client()
    yield
    rc.reset_client()


class TestFallbackSelection:
    def test_uses_real_redis_when_ping_succeeds(self):
        # A genuine redis.Redis (pointed at a closed port) whose ping is stubbed,
        # so the isinstance() check in is_redis_backed() is exercised properly.
        fake = redis.Redis.from_url("redis://127.0.0.1:1/0")

        with (
            patch("app.config.settings") as mock_settings,
            patch.object(redis.Redis, "from_url", return_value=fake),
            patch.object(fake, "ping", return_value=True),
        ):
            mock_settings.REDIS_URL = "redis://real-host:6379/0"
            client = rc.get_client()
            # Assert inside the block: get_client() caches, but settings do not
            # outlive the patch context.
            assert client is fake
            assert rc.is_redis_backed() is True

    def test_falls_back_to_memory_when_ping_raises_connection_error(self):
        fake = MagicMock()
        fake.ping.side_effect = RedisConnectionError("Name or service not known")

        with (
            patch("app.config.settings") as mock_settings,
            patch.object(redis.Redis, "from_url", return_value=fake),
        ):
            mock_settings.REDIS_URL = (
                "redis://default:pw@seat-tomatoes-silver-90462.db.redis.io:19302"
            )
            client = rc.get_client()
            assert isinstance(client, InMemoryRedis)
            assert rc.is_redis_backed() is False

    def test_fallback_still_supports_cache_operations(self):
        fake = MagicMock()
        fake.ping.side_effect = RedisConnectionError("down")

        with (
            patch("app.config.settings") as mock_settings,
            patch.object(redis.Redis, "from_url", return_value=fake),
        ):
            mock_settings.REDIS_URL = "redis://dead-host:6379/0"
            client = rc.get_client()

        client.setex("profile:octocat", 300, {"grade": "A"})
        assert client.get("profile:octocat") == {"grade": "A"}

    def test_client_is_cached_across_calls(self):
        fake = MagicMock()
        fake.ping.return_value = True

        with (
            patch("app.config.settings") as mock_settings,
            patch.object(redis.Redis, "from_url", return_value=fake) as mock_from_url,
        ):
            mock_settings.REDIS_URL = "redis://real-host:6379/0"
            first = rc.get_client()
            second = rc.get_client()

        assert first is second
        # Connection is established once, not per request
        mock_from_url.assert_called_once()

    def test_reset_client_forces_a_reprobe(self):
        fake = MagicMock()
        fake.ping.return_value = True

        with (
            patch("app.config.settings") as mock_settings,
            patch.object(redis.Redis, "from_url", return_value=fake) as mock_from_url,
        ):
            mock_settings.REDIS_URL = "redis://real-host:6379/0"
            rc.get_client()
            rc.reset_client()
            rc.get_client()

        assert mock_from_url.call_count == 2

    def test_connection_is_built_with_a_short_timeout(self):
        fake = MagicMock()
        fake.ping.return_value = True

        with (
            patch("app.config.settings") as mock_settings,
            patch.object(redis.Redis, "from_url", return_value=fake) as mock_from_url,
        ):
            mock_settings.REDIS_URL = "redis://real-host:6379/0"
            rc.get_client()

        _, kwargs = mock_from_url.call_args
        # Prevents a request thread hanging on an unresolvable host
        assert kwargs["socket_connect_timeout"] == rc.REDIS_CONNECT_TIMEOUT
        assert kwargs["socket_timeout"] == rc.REDIS_CONNECT_TIMEOUT
