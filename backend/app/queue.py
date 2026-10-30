"""Job queue abstraction with an in-process fallback.

Analysis is normally dispatched to an RQ worker backed by Redis. When Redis is
unavailable, :mod:`app.cache.redis_client` selects an in-process store, and this
module dispatches the same task onto a local thread pool instead.

Both backends expose the same surface used by the API layer:

``queue.enqueue(func, *args) -> job_handle``  (handle has ``.id``)
``Job.fetch(job_id, connection=...) -> job``  (``get_status()``, ``result``, ``exc_info``)
"""

import logging
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from rq.exceptions import NoSuchJobError

from app.cache.redis_client import get_client, is_redis_backed

logger = logging.getLogger(__name__)

# How long a finished/failed job record lingers before being discarded.
JOB_TTL_SECONDS = 3600

# Local fallback runs jobs in-process; keep concurrency modest because GitHub
# aggregation is network-bound and we do not want to hammer the API.
LOCAL_MAX_WORKERS = 4

_executor = ThreadPoolExecutor(
    max_workers=LOCAL_MAX_WORKERS,
    thread_name_prefix="local-worker",
)


def _job_key(job_id: str) -> str:
    return f"rq:job:{job_id}"


class LocalJob:
    """Stand-in for ``rq.job.Job`` backed by the in-memory store."""

    def __init__(self, job_id: str, record: dict[str, Any]) -> None:
        self.id = job_id
        self._record = record

    @classmethod
    def fetch(cls, job_id: str, connection: Any = None) -> "LocalJob":
        record = get_client().get(_job_key(job_id))
        if record is None:
            raise NoSuchJobError(f"No such job: {job_id}")
        return cls(job_id, record)

    def get_status(self, refresh: bool = False) -> str:
        return self._record.get("status", "queued")

    @property
    def result(self) -> Any:
        return self._record.get("result")

    @property
    def exc_info(self) -> str | None:
        return self._record.get("exc_info")

    def cancel(self) -> None:
        self._record["status"] = "canceled"


class LocalQueue:
    """Stand-in for ``rq.Queue`` that runs jobs on a local thread pool."""

    def __init__(self, name: str = "default") -> None:
        self.name = name

    def enqueue(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> LocalJob:
        client = get_client()
        job_id = uuid.uuid4().hex
        record: dict[str, Any] = {"status": "queued", "result": None, "exc_info": None}
        client.setex(_job_key(job_id), JOB_TTL_SECONDS, record)

        def _run() -> None:
            record["status"] = "started"
            try:
                record["result"] = func(*args, **kwargs)
                record["status"] = "finished"
            except Exception:  # noqa: BLE001 - job failure is recorded, not raised
                record["exc_info"] = traceback.format_exc()
                record["status"] = "failed"
                logger.exception("In-process analysis job %s failed", job_id)
            finally:
                # Refresh TTL so a long job is not evicted mid-flight.
                client.setex(_job_key(job_id), JOB_TTL_SECONDS, record)

        _executor.submit(_run)
        return LocalJob(job_id, record)


def _resolve_queue() -> Any:
    if is_redis_backed():
        from redis import Redis
        from rq import Queue

        return Queue("default", connection=get_client())

    logger.info("Using in-process job queue (Redis unavailable).")
    return LocalQueue("default")


def _resolve_job_class() -> Any:
    if is_redis_backed():
        from rq.job import Job

        return Job
    return LocalJob


queue = _resolve_queue()
Job = _resolve_job_class()
