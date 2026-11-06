"""
Strict Unit Test Suite for ResilientLRUCache.
Executed by Agent 5 (Strict QA & Bug Tester).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import time
import threading
from src.cache_core import ResilientLRUCache, CacheCapacityError


class TestResilientLRUCache(unittest.TestCase):

    def setUp(self):
        self.cache = ResilientLRUCache(capacity=3, default_ttl=None)

    def test_basic_put_and_get(self):
        self.cache.put("a", 100)
        self.cache.put("b", 200)
        self.assertEqual(self.cache.get("a"), 100)
        self.assertEqual(self.cache.get("b"), 200)
        self.assertIsNone(self.cache.get("non_existent"))

    def test_lru_eviction(self):
        self.cache.put("k1", "v1")
        self.cache.put("k2", "v2")
        self.cache.put("k3", "v3")
        # Touch k1 to make it most recently used
        self.cache.get("k1")
        # Adding 4th item should evict k2 (least recently used)
        self.cache.put("k4", "v4")
        self.assertIsNone(self.cache.get("k2"), "k2 should have been evicted")
        self.assertEqual(self.cache.get("k1"), "v1")
        self.assertEqual(self.cache.get("k3"), "v3")
        self.assertEqual(self.cache.get("k4"), "v4")
        self.assertEqual(self.cache.size(), 3)

    def test_invalid_capacity(self):
        with self.assertRaises(CacheCapacityError):
            ResilientLRUCache(capacity=0)
        with self.assertRaises(CacheCapacityError):
            ResilientLRUCache(capacity=-5)

    def test_ttl_expiration(self):
        ttl_cache = ResilientLRUCache(capacity=5)
        ttl_cache.put("short_lived", "alive", ttl=0.1)
        self.assertEqual(ttl_cache.get("short_lived"), "alive")
        time.sleep(0.15)
        self.assertIsNone(ttl_cache.get("short_lived"), "Item should have expired")

    def test_delete_and_clear(self):
        self.cache.put("x", 1)
        self.assertTrue(self.cache.delete("x"))
        self.assertFalse(self.cache.delete("x"))
        self.cache.put("y", 2)
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)

    def test_thread_safety_concurrency(self):
        con_cache = ResilientLRUCache(capacity=50)
        errors = []

        def worker(worker_id: int):
            try:
                for i in range(50):
                    key = f"key_{worker_id}_{i}"
                    con_cache.put(key, i)
                    val = con_cache.get(key)
                    self.assertIn(val, (i, None))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(tid,)) for tid in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent execution generated errors: {errors}")
        self.assertLessEqual(con_cache.size(), 50)


if __name__ == "__main__":
    unittest.main()
