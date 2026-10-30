"""Thread-safe in-process stand-in for the small Redis surface this app uses.

Used automatically when a real Redis server cannot be reached (for example when
``REDIS_URL`` points at a deleted or expired managed instance). It implements
only the commands the application actually calls:

``get`` / ``setex`` / ``set`` / ``exists`` / ``delete`` / ``ping`` / ``ttl``

Values are stored as plain Python objects rather than JSON strings so callers do
not have to change their serialization behaviour when running without Redis.
"""

import threading
import time as _time
from typing import Any

# Cap the number of live keys so a long-lived process cannot grow without bound.
DEFAULT_MAX_KEYS = 2048


class InMemoryRedis:
    """Minimal Redis-compatible store backed by a dict, with TTL support."""

    def __init__(self, max_keys: int = DEFAULT_MAX_KEYS) -> None:
        # key -> (value, expires_at or None)
        self._data: dict[str, tuple[Any, float | None]] = {}
        self._lock = threading.RLock()
        self._max_keys = max_keys

    # ---- internals -------------------------------------------------

    def _expired(self, expires_at: float | None) -> bool:
        return expires_at is not None and expires_at <= _time.time()

    def _purge_expired(self) -> None:
        for key in [k for k, (_, exp) in self._data.items() if self._expired(exp)]:
            self._data.pop(key, None)

    def _enforce_capacity(self) -> None:
        """Evict soonest-expiring keys once the store is over capacity."""
        overflow = len(self._data) - self._max_keys
        if overflow <= 0:
            return

        # Soonest-expiring entries go first: they would disappear on their own
        # soonest, so dropping them loses the least. Keys without a TTL are
        # sorted last (as infinity) and are preserved longest.
        ordered = sorted(
            self._data.items(),
            key=lambda item: item[1][1] if item[1][1] is not None else float("inf"),
        )
        for key, _ in ordered[:overflow]:
            self._data.pop(key, None)

    def _set(self, name: str, value: Any, expires_at: float | None) -> bool:
        with self._lock:
            self._purge_expired()
            self._data[name] = (value, expires_at)
            self._enforce_capacity()
        return True

    # ---- Redis-compatible commands --------------------------------

    def ping(self) -> bool:
        return True

    def get(self, name: str) -> Any:
        with self._lock:
            entry = self._data.get(name)
            if entry is None:
                return None
            value, expires_at = entry
            if self._expired(expires_at):
                self._data.pop(name, None)
                return None
            return value

    def setex(self, name: str, time: int, value: Any) -> bool:
        """Mirror ``redis-py``: ``time`` is a TTL in seconds."""
        return self._set(name, value, _time.time() + float(time))

    def set(self, name: str, value: Any, ex: int | None = None) -> bool:
        expires_at = _time.time() + float(ex) if ex is not None else None
        return self._set(name, value, expires_at)

    def exists(self, name: str) -> int:
        return 1 if self.get(name) is not None else 0

    def delete(self, *names: str) -> int:
        removed = 0
        with self._lock:
            for name in names:
                if self._data.pop(name, None) is not None:
                    removed += 1
        return removed

    def ttl(self, name: str) -> int:
        """Seconds until expiry; ``-1`` when persistent, ``-2`` when missing."""
        with self._lock:
            entry = self._data.get(name)
            if entry is None:
                return -2
            _, expires_at = entry
            if expires_at is None:
                return -1
            remaining = expires_at - _time.time()
            if remaining <= 0:
                return -2
            return int(remaining)
