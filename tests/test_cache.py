"""
tests/test_cache.py
-------------------
Unit tests for the caching module (Redis with in-memory RAM fallback).
"""

import unittest
from utils import cache


class TestCache(unittest.TestCase):

    def setUp(self):
        self.cache = cache

    def test_cache_set_and_get(self):
        key = "test:symbol:AAPL"
        val = '{"symbol": "AAPL", "price": 190.0}'
        self.cache.set(key, val, ttl=10)

        result = self.cache.get(key)
        self.assertEqual(result, val)

    def test_cache_miss_returns_none(self):
        result = self.cache.get("non_existent_key_12345")
        self.assertIsNone(result)

    def test_cache_delete(self):
        key = "test:delete_key"
        self.cache.set(key, "data", ttl=10)
        self.assertEqual(self.cache.get(key), "data")

        self.cache.delete(key)
        self.assertIsNone(self.cache.get(key))

    def test_cache_ttl(self):
        key = "test:ttl_key"
        self.cache.set(key, "data", ttl=30)
        ttl = self.cache.ttl(key)
        self.assertTrue(0 < ttl <= 30)


if __name__ == "__main__":
    unittest.main()
