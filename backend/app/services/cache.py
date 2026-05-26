"""
ShelfIQ Backend — Redis Caching Layer.

TTL-based caching for hot data:
- Shelf state:       30 seconds
- Forecast results:  1 hour
- Festival impact:   24 hours
- Compliance scores: 5 minutes

Falls back to a simple dict cache if Redis is unavailable.
"""
import json
import hashlib
from typing import Any, Optional

from backend.app.core.config import settings


class CacheService:
    """Redis-backed cache with in-memory fallback."""

    # TTLs in seconds
    TTL_SHELF_STATE = 30
    TTL_FORECAST = 3600        # 1 hour
    TTL_FESTIVAL = 86400       # 24 hours
    TTL_COMPLIANCE = 300       # 5 minutes
    TTL_DEFAULT = 60

    def __init__(self):
        self._redis = None
        self._fallback: dict[str, Any] = {}
        self._use_redis = False

    async def connect(self) -> None:
        """Try to connect to Redis."""
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await self._redis.ping()
            self._use_redis = True
        except Exception:
            self._use_redis = False

    async def get(self, key: str) -> Optional[str]:
        """Get a cached value."""
        if self._use_redis and self._redis:
            try:
                return await self._redis.get(key)
            except Exception:
                pass
        return self._fallback.get(key)

    async def set(self, key: str, value: Any, ttl: int = TTL_DEFAULT) -> None:
        """Set a cached value with TTL."""
        serialized = json.dumps(value, default=str) if not isinstance(value, str) else value

        if self._use_redis and self._redis:
            try:
                await self._redis.setex(key, ttl, serialized)
                return
            except Exception:
                pass
        self._fallback[key] = serialized

    async def delete(self, key: str) -> None:
        """Delete a cached key."""
        if self._use_redis and self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass
        self._fallback.pop(key, None)

    async def bust_pattern(self, pattern: str) -> None:
        """Delete all keys matching a pattern (Redis only)."""
        if self._use_redis and self._redis:
            try:
                keys = []
                async for key in self._redis.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await self._redis.delete(*keys)
            except Exception:
                pass

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    @property
    def status(self) -> str:
        return "redis" if self._use_redis else "in-memory"

    # ── Key builders ─────────────────────────────────────────

    @staticmethod
    def shelf_key(store_id: str) -> str:
        return f"cache:shelf:{store_id}"

    @staticmethod
    def forecast_key(sku_id: str, store_id: str) -> str:
        return f"cache:forecast:{store_id}:{sku_id}"

    @staticmethod
    def festival_key() -> str:
        return "cache:festivals:upcoming"

    @staticmethod
    def compliance_key(store_id: str) -> str:
        return f"cache:compliance:{store_id}"


# Singleton
cache = CacheService()
