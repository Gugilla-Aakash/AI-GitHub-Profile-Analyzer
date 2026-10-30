import importlib.util
import pathlib
import runpy
import sys
import types
from unittest.mock import MagicMock

import pytest

# Dynamically resolve root-level worker.py whether tests run from root or tests/
_worker_file = pathlib.Path(__file__).parent / "worker.py"
if not _worker_file.exists():
    _worker_file = pathlib.Path(__file__).parent.parent / "worker.py"
WORKER_PATH = str(_worker_file.resolve())


def _run_worker_script(monkeypatch, redis_ping_fails: bool = False):
    # worker.py runs real redis/rq connections when executed for real, so we
    # swap those modules out in sys.modules before running the script

    # The worker imports RedisError from redis.exceptions for its ping guard,
    # so the injected failure must be an instance of that same fake class.
    fake_exceptions_module = types.ModuleType("redis.exceptions")

    class _RedisError(Exception):
        pass

    fake_exceptions_module.RedisError = _RedisError

    fake_redis_conn = MagicMock()
    fake_redis_conn.ping.side_effect = (
        _RedisError("Name or service not known") if redis_ping_fails else None
    )
    fake_redis_module = types.ModuleType("redis")
    redis_cls_mock = MagicMock()
    redis_cls_mock.from_url.return_value = fake_redis_conn
    fake_redis_module.Redis = redis_cls_mock
    fake_redis_module.exceptions = fake_exceptions_module

    fake_queue_cls = MagicMock()
    fake_worker_instance = MagicMock()
    fake_worker_cls = MagicMock(return_value=fake_worker_instance)

    fake_rq_module = types.ModuleType("rq")
    fake_rq_module.Queue = fake_queue_cls
    fake_rq_module.Worker = fake_worker_cls

    fake_settings = MagicMock()
    fake_settings.REDIS_URL = "redis://fake-host:6379/0"

    fake_redis_client_module = types.ModuleType("app.cache.redis_client")
    fake_redis_client_module.REDIS_CONNECT_TIMEOUT = 2

    fake_config_module = types.ModuleType("app.config")
    fake_config_module.settings = fake_settings

    fake_cache_module = types.ModuleType("app.cache")

    fake_app_module = types.ModuleType("app")
    fake_app_module.config = fake_config_module
    fake_app_module.cache = fake_cache_module

    monkeypatch.setitem(sys.modules, "redis", fake_redis_module)
    monkeypatch.setitem(sys.modules, "redis.exceptions", fake_exceptions_module)
    monkeypatch.setitem(sys.modules, "rq", fake_rq_module)
    monkeypatch.setitem(sys.modules, "app", fake_app_module)
    monkeypatch.setitem(sys.modules, "app.cache", fake_cache_module)
    monkeypatch.setitem(
        sys.modules, "app.cache.redis_client", fake_redis_client_module
    )
    monkeypatch.setitem(sys.modules, "app.config", fake_config_module)

    runpy.run_path(WORKER_PATH, run_name="__main__")

    return {
        "redis_module": fake_redis_module,
        "redis_conn": fake_redis_conn,
        "queue_cls": fake_queue_cls,
        "worker_cls": fake_worker_cls,
        "worker_instance": fake_worker_instance,
        "settings": fake_settings,
    }


def test_redis_connection_created_with_correct_options(monkeypatch):
    result = _run_worker_script(monkeypatch)
    result["redis_module"].Redis.from_url.assert_called_once_with(
        "redis://fake-host:6379/0",
        socket_connect_timeout=2,
        socket_keepalive=True,
        health_check_interval=30,
    )


def test_worker_exits_cleanly_when_redis_is_unreachable(monkeypatch):
    # A dead Redis (expired instance, bad DNS) must not crash-loop the
    # supervisor; the worker should exit(1) before constructing RQ objects.
    with pytest.raises(SystemExit) as exc_info:
        _run_worker_script(monkeypatch, redis_ping_fails=True)

    assert exc_info.value.code == 1


def test_queue_created_for_default_listen_list(monkeypatch):
    result = _run_worker_script(monkeypatch)
    result["queue_cls"].assert_called_once_with(
        "default", connection=result["redis_conn"]
    )


def test_worker_created_with_queues_and_shared_connection(monkeypatch):
    result = _run_worker_script(monkeypatch)
    result["worker_cls"].assert_called_once()
    call_args = result["worker_cls"].call_args
    assert call_args.kwargs["connection"] == result["redis_conn"]
    # first positional arg is the list of queue instances
    queues_passed = call_args.args[0]
    assert len(queues_passed) == 1


def test_worker_work_is_called_to_start_processing(monkeypatch):
    result = _run_worker_script(monkeypatch)
    result["worker_instance"].work.assert_called_once()


def test_script_does_not_run_anything_when_imported_not_executed():
    # importing worker.py as a plain module (not run as __main__) should not
    # touch redis or rq at all, since everything lives under the __main__ guard
    spec = importlib.util.spec_from_file_location("worker_import_check", WORKER_PATH)
    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    # this will fail if it tries to actually import real redis/rq/app.config
    # and those aren't installed/available, which is exactly what we want to
    # confirm doesn't happen just from importing
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError:
        # if redis/rq/app aren't installed in this environment at all, that's
        # fine, the point of this test is just that nothing under __main__ ran
        pass
    assert not hasattr(module, "worker")
