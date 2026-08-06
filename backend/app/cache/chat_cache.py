import json
import logging
from typing import Any

import redis

from app.config import settings

logger = logging.getLogger(__name__)


class ChatCache:
    """Redis storage for multi turn chat sessions"""

    PREFIX = "chat:"

    def __init__(self) -> None:
        self.redis = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        self.ttl = settings.CACHE_TTL

    def _key(self, session_id: str) -> str:
        return f"{self.PREFIX}{session_id.strip()}"

    def save_session(
        self,
        session_id: str,
        username: str,
        context: str,
        history: list[dict[str, str]],
    ) -> None:
        """Saves or updates a chat session in Redis with TTL"""
        payload = {
            "username": username,
            "context": context,
            "history": history,
        }

        self.redis.setex(
            self._key(session_id),
            self.ttl,
            json.dumps(payload),
        )

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve and deserialize a chat session, returns None if missing or corrupted"""
        raw = self.redis.get(self._key(session_id))

        if raw is None:
            return None

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to decode session '%s': %s", session_id, exc)
            return None

    def append_messages(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Appends a user (or) assistant turn to history and resets the TTL"""
        session = self.get_session(session_id)

        if session is None:
            raise ValueError(f"Chat session '{session_id}' not found.")

        history = session.get("history", [])

        if user_message:
            history.append({"role": "user", "content": user_message})

        if assistant_message:
            history.append({"role": "assistant", "content": assistant_message})

        self.save_session(
            session_id=session_id,
            username=session.get("username", ""),
            context=session.get("context", ""),
            history=history,
        )

    def is_gemini_disabled(self) -> bool:
        """Checks if Gemini is currently in a rate limit cooldown."""
        return bool(self.redis.exists("llm:gemini_disabled"))

    def disable_gemini(self, ttl: int = 300) -> None:
        """Temporarily disables Gemini during provider fallback events"""
        self.redis.setex("llm:gemini_disabled", ttl, "1")
