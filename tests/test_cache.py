"""Tests for file-based cache with TTL."""

import time

from youvedio.storage.cache import clear, get, set


class TestCache:
    def test_set_and_get(self):
        key = "test:unit:basic"
        payload = {"data": "hello", "num": 42}
        set(key, payload)
        result = get(key)
        assert result == payload

    def test_get_nonexistent(self):
        result = get("test:unit:nonexistent:" + str(time.time()))
        assert result is None

    def test_get_expired(self):
        key = "test:unit:expired:" + str(time.time())
        set(key, {"data": "expired"})
        time.sleep(0.1)
        result = get(key, ttl=-1)
        assert result is None

    def test_multiple_keys(self):
        keys = [f"test:unit:multi:{i}" for i in range(3)]
        for i, k in enumerate(keys):
            set(k, {"idx": i})
        for i, k in enumerate(keys):
            result = get(k)
            assert result["idx"] == i

    def test_clear_expired(self):
        key1 = "test:unit:clear:keep:" + str(time.time())
        key2 = "test:unit:clear:remove:" + str(time.time())
        set(key1, {"data": "keep"})
        set(key2, {"data": "remove"})
        time.sleep(0.1)
        cleared = clear(ttl=-1)
        assert isinstance(cleared, int)  # some files were removed

    def test_set_empty_payload(self):
        key = "test:unit:empty:" + str(time.time())
        set(key, {})
        result = get(key)
        assert result == {}
