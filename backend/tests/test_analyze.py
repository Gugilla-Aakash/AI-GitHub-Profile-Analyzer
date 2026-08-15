from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError
from rq.exceptions import NoSuchJobError

from app.api.routes import analyze

PATCH_TARGET = "app.api.routes.analyze"


def make_job(job_id="job-123", status="queued", result=None, exc_info=None):
    job = MagicMock()
    job.id = job_id
    job.get_status.return_value = status
    job.result = result
    job.exc_info = exc_info
    return job


# ---- analyze_profile tests ----


def test_returns_cached_result_without_touching_queue():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
    ):
        cache_mock.get_profile.return_value = {"grade": "A"}
        result = analyze.analyze_profile("Octocat")
    assert result["status"] == "completed"
    assert result["cached"] is True
    assert result["result"] == {"grade": "A"}
    queue_mock.enqueue.assert_not_called()


def test_denylisted_username_blocked_before_queueing():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
    ):
        cache_mock.get_profile.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            analyze.analyze_profile("GitHub")
    assert exc_info.value.status_code == 400
    # message should reflect the original casing the user typed, not normalized
    assert "'GitHub'" in exc_info.value.detail
    queue_mock.enqueue.assert_not_called()


def test_no_cache_no_lock_enqueues_new_job():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.redis_conn") as redis_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
    ):
        cache_mock.get_profile.return_value = None
        redis_mock.get.return_value = None
        queue_mock.enqueue.return_value = make_job(job_id="new-job-1")

        result = analyze.analyze_profile("someuser")

    assert result["status"] == "queued"
    assert result["job_id"] == "new-job-1"
    queue_mock.enqueue.assert_called_once_with(analyze.analyze_profile_task, "someuser")
    redis_mock.setex.assert_called_once_with("in_progress:someuser", 600, "new-job-1")


def test_existing_lock_but_job_missing_falls_through_to_new_enqueue():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.redis_conn") as redis_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
        patch(f"{PATCH_TARGET}.Job") as job_cls,
    ):
        cache_mock.get_profile.return_value = None
        redis_mock.get.return_value = b"stale-job-id"
        job_cls.fetch.side_effect = NoSuchJobError()
        queue_mock.enqueue.return_value = make_job(job_id="fresh-job")

        result = analyze.analyze_profile("someuser")

    assert result["job_id"] == "fresh-job"
    queue_mock.enqueue.assert_called_once()


def test_existing_job_queued_returns_in_progress_without_enqueueing_again():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.redis_conn") as redis_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
        patch(f"{PATCH_TARGET}.Job") as job_cls,
    ):
        cache_mock.get_profile.return_value = None
        redis_mock.get.return_value = b"existing-job-id"
        job_cls.fetch.return_value = make_job(job_id="existing-job-id", status="queued")

        result = analyze.analyze_profile("someuser")

    assert result["job_id"] == "existing-job-id"
    assert result["status"] == "queued"
    assert "already in progress" in result["message"]
    queue_mock.enqueue.assert_not_called()


def test_existing_job_started_returns_in_progress():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.redis_conn") as redis_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
        patch(f"{PATCH_TARGET}.Job") as job_cls,
    ):
        cache_mock.get_profile.return_value = None
        redis_mock.get.return_value = b"existing-job-id"
        job_cls.fetch.return_value = make_job(
            job_id="existing-job-id", status="started"
        )

        result = analyze.analyze_profile("someuser")

    assert result["status"] == "started"
    queue_mock.enqueue.assert_not_called()


def test_existing_job_finished_enqueues_a_new_one():
    # old job is done, a fresh analysis request should still go through
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.redis_conn") as redis_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
        patch(f"{PATCH_TARGET}.Job") as job_cls,
    ):
        cache_mock.get_profile.return_value = None
        redis_mock.get.return_value = b"old-job-id"
        job_cls.fetch.return_value = make_job(job_id="old-job-id", status="finished")
        queue_mock.enqueue.return_value = make_job(job_id="brand-new-job")

        result = analyze.analyze_profile("someuser")

    assert result["job_id"] == "brand-new-job"
    queue_mock.enqueue.assert_called_once()


def test_redis_error_on_get_returns_503():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.redis_conn") as redis_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
    ):
        cache_mock.get_profile.return_value = None
        redis_mock.get.side_effect = RedisError("connection dropped")

        with pytest.raises(HTTPException) as exc_info:
            analyze.analyze_profile("someuser")

    assert exc_info.value.status_code == 503
    queue_mock.enqueue.assert_not_called()


def test_redis_error_on_enqueue_returns_503():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.redis_conn") as redis_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
    ):
        cache_mock.get_profile.return_value = None
        redis_mock.get.return_value = None
        queue_mock.enqueue.side_effect = RedisError("queue down")

        with pytest.raises(HTTPException) as exc_info:
            analyze.analyze_profile("someuser")

    assert exc_info.value.status_code == 503


def test_redis_error_on_setex_returns_503():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.redis_conn") as redis_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
    ):
        cache_mock.get_profile.return_value = None
        redis_mock.get.return_value = None
        queue_mock.enqueue.return_value = make_job(job_id="job-x")
        redis_mock.setex.side_effect = RedisError("write failed")

        with pytest.raises(HTTPException) as exc_info:
            analyze.analyze_profile("someuser")

    assert exc_info.value.status_code == 503


def test_username_gets_normalized_for_cache_and_lock_lookup():
    with (
        patch(f"{PATCH_TARGET}.cache") as cache_mock,
        patch(f"{PATCH_TARGET}.redis_conn") as redis_mock,
        patch(f"{PATCH_TARGET}.queue") as queue_mock,
    ):
        cache_mock.get_profile.return_value = None
        redis_mock.get.return_value = None
        queue_mock.enqueue.return_value = make_job(job_id="job-x")

        analyze.analyze_profile("  SomeUser  ")

    cache_mock.get_profile.assert_called_once_with("someuser")
    redis_mock.get.assert_called_once_with("in_progress:someuser")


# ---- get_job_status tests ----


def test_job_not_found_returns_404():
    with patch(f"{PATCH_TARGET}.Job") as job_cls:
        job_cls.fetch.side_effect = NoSuchJobError()
        with pytest.raises(HTTPException) as exc_info:
            analyze.get_job_status("missing-job")
    assert exc_info.value.status_code == 404


def test_finished_job_returns_result():
    with patch(f"{PATCH_TARGET}.Job") as job_cls:
        job_cls.fetch.return_value = make_job(status="finished", result={"grade": "S"})
        result = analyze.get_job_status("job-1")
    assert result["status"] == "finished"
    assert result["result"] == {"grade": "S"}


def test_failed_job_user_not_found_returns_404():
    with patch(f"{PATCH_TARGET}.Job") as job_cls:
        job_cls.fetch.return_value = make_job(
            status="failed", exc_info="Traceback...\nUserNotFoundError: nope"
        )
        with pytest.raises(HTTPException) as exc_info:
            analyze.get_job_status("job-1")
    assert exc_info.value.status_code == 404


def test_failed_job_organization_account_returns_404():
    with patch(f"{PATCH_TARGET}.Job") as job_cls:
        job_cls.fetch.return_value = make_job(
            status="failed", exc_info="Organization account cannot be analyzed"
        )
        with pytest.raises(HTTPException) as exc_info:
            analyze.get_job_status("job-1")
    assert exc_info.value.status_code == 404


def test_failed_job_rate_limit_returns_429():
    with patch(f"{PATCH_TARGET}.Job") as job_cls:
        job_cls.fetch.return_value = make_job(
            status="failed", exc_info="RateLimitError: too many requests"
        )
        with pytest.raises(HTTPException) as exc_info:
            analyze.get_job_status("job-1")
    assert exc_info.value.status_code == 429


def test_failed_job_timeout_returns_504():
    with patch(f"{PATCH_TARGET}.Job") as job_cls:
        job_cls.fetch.return_value = make_job(
            status="failed", exc_info="RequestTimeoutError: took too long"
        )
        with pytest.raises(HTTPException) as exc_info:
            analyze.get_job_status("job-1")
    assert exc_info.value.status_code == 504


def test_failed_job_unknown_reason_returns_500():
    with patch(f"{PATCH_TARGET}.Job") as job_cls:
        job_cls.fetch.return_value = make_job(
            status="failed", exc_info="ValueError: something weird broke"
        )
        with pytest.raises(HTTPException) as exc_info:
            analyze.get_job_status("job-1")
    assert exc_info.value.status_code == 500


def test_failed_job_with_no_exc_info_returns_500():
    # exc_info missing entirely, "or ''" fallback should still hit the generic 500 branch
    with patch(f"{PATCH_TARGET}.Job") as job_cls:
        job_cls.fetch.return_value = make_job(status="failed", exc_info=None)
        with pytest.raises(HTTPException) as exc_info:
            analyze.get_job_status("job-1")
    assert exc_info.value.status_code == 500


def test_in_progress_job_returns_status_message():
    with patch(f"{PATCH_TARGET}.Job") as job_cls:
        job_cls.fetch.return_value = make_job(status="started")
        result = analyze.get_job_status("job-1")
    assert result["status"] == "started"
    assert "still in progress" in result["message"]
