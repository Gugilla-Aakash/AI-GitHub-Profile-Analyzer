import time

import pytest

from app.cache.memory_store import InMemoryRedis


class TestBasics:
    def test_ping_returns_true(self):
        assert InMemoryRedis().ping() is True

    def test_get_missing_key_returns_none(self):
        assert InMemoryRedis().get("missing") is None

    def test_setex_then_get_roundtrips_value(self):
        store = InMemoryRedis()
        store.setex("profile:octocat", 300, {"grade": "A"})
        assert store.get("profile:octocat") == {"grade": "A"}

    def test_setex_accepts_keyword_arguments_like_redis_py(self):
        # simple_cache calls setex(name=..., time=..., value=...)
        store = InMemoryRedis()
        store.setex(name="profile:x", time=60, value="v")
        assert store.get("profile:x") == "v"

    def test_set_without_expiry_persists(self):
        store = InMemoryRedis()
        store.set("key", "value")
        assert store.get("key") == "value"
        assert store.ttl("key") == -1

    def test_set_with_ex_expiry(self):
        store = InMemoryRedis()
        store.set("key", "value", ex=60)
        assert store.ttl("key") > 0

    def test_exists_returns_int_like_redis(self):
        store = InMemoryRedis()
        store.setex("a", 60, 1)
        assert store.exists("a") == 1
        assert store.exists("b") == 0

    def test_delete_removes_key(self):
        store = InMemoryRedis()
        store.setex("a", 60, 1)
        assert store.delete("a") == 1
        assert store.get("a") is None
        assert store.delete("a") == 0

    def test_delete_accepts_multiple_keys(self):
        store = InMemoryRedis()
        store.setex("a", 60, 1)
        store.setex("b", 60, 1)
        assert store.delete("a", "b") == 2


class TestExpiry:
    def test_expired_key_returns_none(self):
        store = InMemoryRedis()
        store.setex("a", -1, "value")
        assert store.get("a") is None

    def test_expired_key_reports_zero_exists(self):
        store = InMemoryRedis()
        store.setex("a", -1, "value")
        assert store.exists("a") == 0

    def test_expired_key_reports_ttl_minus_two(self):
        store = InMemoryRedis()
        store.setex("a", -1, "value")
        assert store.ttl("a") == -2

    def test_missing_key_reports_ttl_minus_two(self):
        assert InMemoryRedis().ttl("nope") == -2

    def test_live_key_reports_positive_ttl(self):
        store = InMemoryRedis()
        store.setex("a", 60, "v")
        assert 0 < store.ttl("a") <= 60


class TestCapacity:
    def test_evicts_when_over_capacity(self):
        store = InMemoryRedis(max_keys=5)
        for i in range(20):
            store.setex(f"key:{i}", 300, i)

        assert len(store._data) <= 5

    def test_eviction_drops_soonest_expiring_keys_first(self):
        store = InMemoryRedis(max_keys=2)
        store.set("persistent", "v")
        store.setex("short-lived", 30, "v")
        store.setex("longer-lived", 3000, "v")

        # The soonest-expiring key is the least valuable to keep, so it goes
        # first and the non-expiring key survives longest.
        assert store.get("short-lived") is None
        assert store.get("persistent") == "v"

    def test_expired_keys_are_purged_on_write(self):
        store = InMemoryRedis()
        store.setex("stale", -1, "v")
        store.setex("fresh", 300, "v")

        assert "stale" not in store._data


class TestThreadSafety:
    def test_concurrent_writes_do_not_corrupt_state(self):
        import threading

        store = InMemoryRedis()
        errors = []

        def writer(index: int) -> None:
            try:
                for i in range(200):
                    store.setex(f"key:{index}:{i}", 300, i)
                    store.get(f"key:{index}:{i}")
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(n,)) for n in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert errors == []


class TestIsolation:
    def test_separate_instances_do_not_share_state(self):
        a, b = InMemoryRedis(), InMemoryRedis()
        a.setex("key", 60, "value")
        assert b.get("key") is None


@pytest.mark.parametrize("ttl_seconds", [0, -1, -100])
def test_non_positive_ttls_expire_immediately(ttl_seconds):
    store = InMemoryRedis()
    store.setex("key", ttl_seconds, "value")
    assert store.get("key") is None
    time.sleep(0)  # keep the intent explicit; expiry is time-based, not clock-tick
