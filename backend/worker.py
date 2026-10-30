"""RQ worker entrypoint.

Only meaningful when a real Redis server is reachable. When Redis is down the
web process already handles jobs in-process (see :mod:`app.queue`), so this
worker exits with a clear message instead of crash-looping against a host that
does not exist.
"""

import sys

import redis
from redis.exceptions import RedisError
from rq import Queue, Worker

from app.cache.redis_client import REDIS_CONNECT_TIMEOUT
from app.config import settings

listen = ["default"]


def _redis_is_reachable(redis_conn: redis.Redis) -> bool:
    try:
        redis_conn.ping()
    except RedisError as exc:
        print(
            f"Redis is unreachable ({type(exc).__name__}: {exc}). "
            "The RQ worker cannot run. Analysis jobs will be processed "
            "in-process by the web service instead.",
            file=sys.stderr,
        )
        return False
    return True


if __name__ == "__main__":
    # Enable TCP health checks to keep the socket connection alive while idle
    redis_conn = redis.Redis.from_url(
        settings.REDIS_URL,
        socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
        socket_keepalive=True,
        health_check_interval=30,  # Sends PING every 30s to prevent idle disconnects
    )

    if not _redis_is_reachable(redis_conn):
        sys.exit(1)

    worker = Worker(
        [Queue(name, connection=redis_conn) for name in listen],
        connection=redis_conn,
    )

    print("Starting RQ worker...")
    worker.work()
