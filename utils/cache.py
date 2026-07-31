"""
utils/cache.py
--------------
Redis-backed cache with TTL.
Graceful fallback — if Redis is down, the system still works (no cache).

ADR: Why Redis over in-memory dict?
  - Survives app restarts (persistent across sessions)
  - Works across multiple Streamlit worker processes
  - TTL management is built-in — no manual expiry logic
  - Scales to multi-instance deployment without code changes
  - Industry standard — GS uses Redis internally for exactly this
"""

import json
from typing import Optional, Any
import redis

from config import REDIS_HOST, REDIS_PORT, REDIS_DB, CACHE_TTL_STOCK
from utils.logger import get_logger

logger = get_logger(__name__)


class Cache:
    """
    Redis-backed key-value cache with automatic TTL.
    Falls back silently if Redis is unavailable.
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._available = False
        self._connect()

    def _connect(self) -> None:
        try:
            client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2,          # fail fast if Redis is down
                socket_timeout=2,
            )
            client.ping()
            self._client    = client
            self._available = True
            logger.info("Redis connected at %s:%s", REDIS_HOST, REDIS_PORT)
        except Exception as e:
            self._available = False
            logger.warning(
                "Redis unavailable (%s) — running without cache. "
                "Start Redis with: docker run -p 6379:6379 redis",
                str(e),
            )

    @property
    def is_available(self) -> bool:
        return self._available

    def get(self, key: str) -> Optional[str]:
        """Return cached string value or None on miss / error."""
        if not self._available:
            return None
        try:
            value = self._client.get(key)
            if value:
                logger.debug("Cache HIT: %s", key)
            else:
                logger.debug("Cache MISS: %s", key)
            return value
        except Exception as e:
            logger.warning("Cache get failed for key %s: %s", key, str(e))
            return None

    def set(self, key: str, value: str, ttl: int = CACHE_TTL_STOCK) -> bool:
        """Store string value with TTL (seconds). Returns True on success."""
        if not self._available:
            return False
        try:
            self._client.setex(key, ttl, value)
            logger.debug("Cache SET: %s (TTL=%ss)", key, ttl)
            return True
        except Exception as e:
            logger.warning("Cache set failed for key %s: %s", key, str(e))
            return False

    def ttl(self, key: str) -> int:
        """Return seconds remaining for a key (-1 = no TTL, -2 = missing)."""
        if not self._available:
            return -2
        try:
            return self._client.ttl(key)
        except Exception:
            return -2

    def delete(self, key: str) -> None:
        """Manually invalidate a cached key."""
        if not self._available:
            return
        try:
            self._client.delete(key)
            logger.debug("Cache DEL: %s", key)
        except Exception as e:
            logger.warning("Cache delete failed: %s", str(e))


# Module-level singleton — import this, don't instantiate Cache yourself
cache = Cache()
