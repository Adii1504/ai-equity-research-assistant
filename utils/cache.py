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

import time
from typing import Optional, Any, Dict, Tuple
import redis

from config import REDIS_HOST, REDIS_PORT, REDIS_DB, CACHE_TTL_STOCK
from utils.logger import get_logger

logger = get_logger(__name__)


class Cache:
    """
    Redis-backed key-value cache with automatic TTL and in-memory RAM fallback.
    Falls back gracefully to in-memory TTL dictionary if Redis is unavailable.
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._available = False
        self._memory_cache: Dict[str, Tuple[str, float]] = {}  # key -> (value, expire_timestamp)
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
            logger.info(
                "Redis unavailable (%s) — enabled fast in-memory RAM cache fallback.",
                str(e),
            )

    @property
    def is_available(self) -> bool:
        return self._available

    def get(self, key: str) -> Optional[str]:
        """Return cached string value or None on miss / error / expired."""
        if self._available and self._client:
            try:
                value = self._client.get(key)
                if value:
                    logger.debug("Redis cache HIT: %s", key)
                    return value
                logger.debug("Redis cache MISS: %s", key)
            except Exception as e:
                logger.warning("Cache get failed for key %s: %s", key, str(e))

        # Check in-memory fallback
        if key in self._memory_cache:
            val, expire_at = self._memory_cache[key]
            if time.time() < expire_at:
                logger.debug("In-memory cache HIT: %s", key)
                return val
            else:
                del self._memory_cache[key]

        return None

    def set(self, key: str, value: str, ttl: int = CACHE_TTL_STOCK) -> bool:
        """Store string value with TTL (seconds). Returns True on success."""
        # Always populate in-memory fallback
        self._memory_cache[key] = (value, time.time() + ttl)

        if self._available and self._client:
            try:
                self._client.setex(key, ttl, value)
                logger.debug("Redis cache SET: %s (TTL=%ss)", key, ttl)
                return True
            except Exception as e:
                logger.warning("Cache set failed for key %s: %s", key, str(e))
                return True

        logger.debug("In-memory cache SET: %s (TTL=%ss)", key, ttl)
        return True

    def ttl(self, key: str) -> int:
        """Return seconds remaining for a key (-1 = no TTL, -2 = missing)."""
        if self._available and self._client:
            try:
                return self._client.ttl(key)
            except Exception:
                pass

        if key in self._memory_cache:
            _, expire_at = self._memory_cache[key]
            remaining = int(expire_at - time.time())
            return remaining if remaining > 0 else -2

        return -2

    def delete(self, key: str) -> None:
        """Manually invalidate a cached key."""
        if key in self._memory_cache:
            del self._memory_cache[key]

        if self._available and self._client:
            try:
                self._client.delete(key)
                logger.debug("Cache DEL: %s", key)
            except Exception as e:
                logger.warning("Cache delete failed: %s", str(e))


# Module-level singleton — import this, don't instantiate Cache yourself
cache = Cache()
