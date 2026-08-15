from typing import Any

import redis
from fastapi import APIRouter, HTTPException, status
from redis.exceptions import RedisError
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job

from app.cache.simple_cache import cache
from app.config import settings
from app.tasks import analyze_profile_task

router = APIRouter()

# System accounts that should not be analyzed
DENYLIST = {
    "ghost",
    "dependabot",
    "dependabot-preview",
    "github-actions",
    "github",
}

# Connection for rq
redis_conn = redis.Redis.from_url(settings.REDIS_URL)

queue = Queue("default", connection=redis_conn)


@router.post("/{username}")
def analyze_profile(username: str) -> dict[str, Any]:
    # Normalize username
    normalized_username = username.strip().lower()

    # Checking cache first
    cached_profile = cache.get_profile(normalized_username)
    if cached_profile is not None:
        return {
            "status": "completed",
            "cached": True,
            "message": "Profile found in cache",
            "result": cached_profile,
        }
    # Block System accounts
    if normalized_username in DENYLIST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{username}' cannot be analyzed.",
        )
    # Check in-flight job de-duplication
    lock_key = f"in_progress:{normalized_username}"

    try:
        existing_job_id = redis_conn.get(lock_key)
        if existing_job_id:
            if isinstance(existing_job_id, bytes):
                job_id_str = existing_job_id.decode("utf-8")
            else:
                job_id_str = str(existing_job_id)
            try:
                existing_job = Job.fetch(job_id_str, connection=redis_conn)
                if existing_job.get_status() in ["queued", "started"]:
                    return {
                        "job_id": job_id_str,
                        "status": existing_job.get_status(),
                        "message": "Analysis already in progress for this profile.",
                    }
            except NoSuchJobError:
                # Job expired or was cleaned up and proceed to enqueue a new one
                pass

        # Enqueue background job
        job = queue.enqueue(analyze_profile_task, normalized_username)

        # Set in flight lock for 10min
        redis_conn.setex(lock_key, 600, job.id)

        return {
            "job_id": job.id,
            "status": "queued",
            "message": "Analysis queued. Poll /status/{job_id} for updates.",
        }
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect Redis.",
        ) from exc


@router.get("/status/{job_id}")
def get_job_status(job_id: str) -> dict[str, Any]:
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except NoSuchJobError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        ) from exc

    job_status = job.get_status()

    if job_status == "finished":
        return {
            "status": job_status,
            "result": job.result,
        }

    if job_status == "failed":
        # Unpack job traceback to return meaningful HTTP status codes (Gap 1)
        exc_info = job.exc_info or ""

        if "UserNotFoundError" in exc_info or "Organization account" in exc_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GitHub user not found or is an Organization account.",
            )
        if "RateLimitError" in exc_info:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="GitHub API rate limit exceeded. Please try again later.",
            )
        if "RequestTimeoutError" in exc_info:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="GitHub API request timed out.",
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis job failed due to an internal server error.",
        )

    return {
        "status": job_status,
        "message": "Analysis still in progress.",
    }
