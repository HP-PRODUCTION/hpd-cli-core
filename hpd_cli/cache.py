"""Redis client wrapper with auto-detection and in-memory fallback.

Usage:
    from hpd_cli.cache import cache

    # Auto-detects Redis if REDIS_URL is set, otherwise uses dict
    cache.set("key", "value", ttl=60)
    value = cache.get("key")
"""
import os
import time
import json
import threading
from typing import Any, Optional


# === In-memory fallback ====================================

class _MemoryCache:
    """Thread-safe in-memory cache when Redis is unavailable."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            value, expiry = item
            if expiry and time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        expiry = time.time() + ttl if ttl else 0
        with self._lock:
            self._store[key] = (value, expiry)
        return True

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def incr(self, key: str) -> int:
        with self._lock:
            val = self._store.get(key, (0, 0))
            new_val = (val[0] or 0) + 1
            self._store[key] = (new_val, val[1])
            return new_val

    def expire(self, key: str, ttl: int) -> bool:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return False
            self._store[key] = (item[0], time.time() + ttl)
            return True

    def flush(self) -> None:
        with self._lock:
            self._store.clear()


# === Redis wrapper =========================================

class _RedisCache:
    """Redis-based cache. Falls back gracefully if Redis is unreachable."""

    def __init__(self):
        self._redis = None
        self._memory = _MemoryCache()
        self._connect()

    def _connect(self):
        url = os.environ.get("REDIS_URL", "")
        if not url:
            return
        try:
            import redis as _redis
            self._redis = _redis.from_url(url, socket_timeout=2, decode_responses=True)
            self._redis.ping()
        except Exception:
            self._redis = None

    @property
    def available(self) -> bool:
        return self._redis is not None

    def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            return self._memory.get(key)
        try:
            val = self._redis.get(key)
            if val is None:
                return None
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return val
        except Exception:
            return self._memory.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self._redis:
            return self._memory.set(key, value, ttl)
        try:
            val = json.dumps(value) if not isinstance(value, (str, bytes)) else value
            if ttl:
                return self._redis.setex(key, ttl, val)
            return self._redis.set(key, val)
        except Exception:
            return self._memory.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        if not self._redis:
            return self._memory.delete(key)
        try:
            return bool(self._redis.delete(key))
        except Exception:
            return self._memory.delete(key)

    def exists(self, key: str) -> bool:
        if not self._redis:
            return self._memory.exists(key)
        try:
            return bool(self._redis.exists(key))
        except Exception:
            return self._memory.exists(key)

    def incr(self, key: str) -> int:
        if not self._redis:
            return self._memory.incr(key)
        try:
            return self._redis.incr(key)
        except Exception:
            return self._memory.incr(key)

    def expire(self, key: str, ttl: int) -> bool:
        if not self._redis:
            return self._memory.expire(key, ttl)
        try:
            return bool(self._redis.expire(key, ttl))
        except Exception:
            return self._memory.expire(key, ttl)

    def flush(self) -> None:
        if self._redis:
            try:
                self._redis.flushdb()
                return
            except Exception:
                pass
        self._memory.flush()


# === Singleton =============================================

cache = _RedisCache()


# === Rate limiter helpers ==================================

def check_rate_limit(key: str, max_requests: int, window: int) -> tuple[bool, int]:
    """Check if a rate limit has been exceeded.

    Returns (allowed, remaining) where allowed is False if exceeded.
    Uses Redis if available, otherwise in-memory.
    """
    cache_key = f"ratelimit:{key}"
    current = cache.incr(cache_key)
    if current == 1:
        cache.expire(cache_key, window)
    remaining = max(0, max_requests - current)
    return (current <= max_requests, remaining)
