import json
import logging
from typing import Any

import redis

from app.config import settings

logger = logging.getLogger(__name__)


class SimpleCache:
    """Redis-backed profile cache wrapper."""

    def __init__(self) -> None:
        """Initializes the Redis client using the configured Redis URL."""
        self.client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )

    def _get_key(self, username: str) -> str:
        """Generates a namespaced and case-insensitive Redis key."""
        return f"profile:{username.strip().lower()}"

    def set_profile(self, username: str, data: dict[str, Any]) -> None:
        """Serializes data to JSON and stores it with TTL."""
        key = self._get_key(username)
        serialized_data = json.dumps(data)
        self.client.setex(
            name=key,
            time=settings.CACHE_TTL,
            value=serialized_data,
        )

    def get_profile(self, username: str) -> dict[str, Any] | None:
        """Retrieves and deserializes data, returning None if key is missing or invalid."""
        key = self._get_key(username)
        cached_data = self.client.get(key)

        if cached_data is None:
            return None

        try:
            return json.loads(cached_data)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to decode cached profile for %s: %s", username, exc)
            return None


# Instantiate singleton for the application to share
cache = SimpleCache()
