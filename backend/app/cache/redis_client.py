"""Redis connection factory with an in-memory fallback.

The application's entire Redis dependency (profile cache, chat sessions, job
locks, RQ queue) is served by whichever backend this module selects:

* a real ``redis.Redis`` connection, when the configured server answers a
  ``PING`` within ``REDIS_CONNECT_TIMEOUT`` seconds;
* an in-process :class:`~app.cache.memory_store.InMemoryRedis`, otherwise.

Why the fallback exists: a managed Redis instance can disappear out from under
a deployment (expired free tier, revoked credentials, DNS for a deleted host).
Previously that turned every analysis into an unhandled ``ConnectionError`` and
a ``500``. With this module the API stays fully functional on a single host and
recovers automatically on the next restart once Redis is reachable again.

Degradation is intentional and logged loudly at startup so it is never silent.
"""

import logging

import redis

from app.cache.memory_store import InMemoryRedis
from app.config import settings

logger = logging.getLogger(__name__)

# Fail fast rather than hanging a request thread on an unresolvable host.
REDIS_CONNECT_TIMEOUT = 2

_client = None


def _build_real_client() -> redis.Redis | None:
    """Return a live Redis client, or ``None`` if the server is unusable."""
    client = redis.Redis.from_url(
        settings.REDIS_URL,
        socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
        socket_timeout=REDIS_CONNECT_TIMEOUT,
        socket_keepalive=True,
        health_check_interval=30,
    )
    try:
        client.ping()
    except redis.RedisError as exc:
        logger.warning(
            "Redis unreachable at startup (%s: %s). Falling back to the "
            "in-memory store: caching, job locks and chat sessions will not "
            "survive a restart, and background jobs run in-process instead of "
            "via RQ.",
            type(exc).__name__,
            exc,
        )
        return None
    return client


def get_client() -> redis.Redis | InMemoryRedis:
    """Return the process-wide Redis client or its in-memory stand-in."""
    global _client
    if _client is None:
        _client = _build_real_client() or InMemoryRedis()
        if isinstance(_client, redis.Redis):
            logger.info("Connected to Redis at %s", _client.connection_pool)
    return _client


def is_redis_backed() -> bool:
    """True when a real Redis server is in use, False for the in-memory fallback."""
    return isinstance(get_client(), redis.Redis)


def reset_client() -> None:
    """Drop the cached client so the next call re-probes. Used by tests."""
    global _client
    _client = None
