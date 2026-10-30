import time

import pytest
from rq.exceptions import NoSuchJobError

from app.cache.memory_store import InMemoryRedis
from app.queue import LocalJob, LocalQueue


@pytest.fixture
def store(monkeypatch):
    """Force the local queue to operate on an isolated in-memory store."""
    fake = InMemoryRedis()

    def _task(username):
        return {"username": username, "grade": "A"}

    monkeypatch.setattr("app.queue.get_client", lambda: fake)
    return fake, _task


def _wait_for(job: LocalJob, timeout: float = 5.0) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = job.get_status()
        if status in ("finished", "failed"):
            return status
        time.sleep(0.01)
    return job.get_status()


class TestLocalQueue:
    def test_enqueue_returns_a_job_with_an_id(self, store):
        _, task = store
        job = LocalQueue().enqueue(task, "octocat")

        assert isinstance(job, LocalJob)
        assert isinstance(job.id, str) and len(job.id) > 0

    def test_job_reaches_finished_status(self, store):
        _, task = store
        job = LocalQueue().enqueue(task, "octocat")

        assert _wait_for(job) == "finished"

    def test_job_result_is_the_return_value(self, store):
        _, task = store
        job = LocalQueue().enqueue(task, "octocat")
        _wait_for(job)

        assert job.result == {"username": "octocat", "grade": "A"}

    def test_failing_job_is_recorded_not_raised(self, store):
        def boom(_username):
            raise ValueError("analysis exploded")

        job = LocalQueue().enqueue(boom, "octocat")
        assert _wait_for(job) == "failed"

    def test_failed_job_exposes_traceback(self, store):
        def boom(_username):
            raise ValueError("analysis exploded")

        job = LocalQueue().enqueue(boom, "octocat")
        _wait_for(job)

        # analyze.py maps these substrings to 404 / 429 / 504 responses
        assert "ValueError: analysis exploded" in job.exc_info
        assert job.result is None

    def test_queue_name_defaults_to_default(self, store):
        assert LocalQueue().name == "default"


class TestLocalJobFetch:
    def test_fetch_returns_the_stored_job(self, store):
        fake, task = store
        job = LocalQueue().enqueue(task, "octocat")
        _wait_for(job)

        fetched = LocalJob.fetch(job.id, connection=fake)
        assert fetched.id == job.id
        assert fetched.get_status() == "finished"

    def test_fetch_unknown_id_raises_no_such_job_error(self, store):
        fake, _ = store
        with pytest.raises(NoSuchJobError):
            LocalJob.fetch("missing-job", connection=fake)

    def test_fetch_ignores_connection_argument(self, store):
        """The store is resolved from the factory, not the passed connection."""
        fake, task = store
        job = LocalQueue().enqueue(task, "octocat")
        _wait_for(job)

        assert LocalJob.fetch(job.id, connection=None).id == job.id

    def test_job_record_expires(self, store):
        fake, task = store
        job = LocalQueue().enqueue(task, "octocat")
        _wait_for(job)

        fake.delete(f"rq:job:{job.id}")
        with pytest.raises(NoSuchJobError):
            LocalJob.fetch(job.id, connection=fake)

    def test_cancel_marks_job_canceled(self, store):
        _, task = store
        job = LocalQueue().enqueue(task, "octocat")

        job.cancel()
        assert job.get_status() == "canceled"
