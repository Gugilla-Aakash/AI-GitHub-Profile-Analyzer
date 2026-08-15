import redis
from rq import Queue, Worker

from app.config import settings

listen = ["default"]

if __name__ == "__main__":
    # Enable TCP health checks to keep the socket connection alive while idle
    redis_conn = redis.Redis.from_url(
        settings.REDIS_URL,
        health_check_interval=30,  # Sends PING every 30s to prevent idle disconnects
        socket_connect_timeout=10,
        socket_timeout=30,  # Bail out of a stalled read/write instead of hanging forever
    )

    worker = Worker(
        [Queue(name, connection=redis_conn) for name in listen],
        connection=redis_conn,
    )

    print("Starting RQ worker...")
    worker.work()
