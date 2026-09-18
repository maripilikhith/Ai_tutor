"""
AI Study Companion — Redis Cache Client

Provides caching and rate limiting via Upstash Redis.
Gracefully degrades — if Redis is unavailable, operations silently fail
and the app continues without caching (just slower).
"""

import json
import hashlib
from typing import Any
from app.config import get_settings

# Try to import upstash_redis, gracefully handle if not available
try:
    from upstash_redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

_client = None


def get_redis():
    """Get or create the Redis client. Returns None if Redis is unavailable."""
    global _client
    if not REDIS_AVAILABLE:
        return None

    if _client is None:
        settings = get_settings()
        if settings.upstash_redis_url and settings.upstash_redis_token:
            try:
                _client = Redis(
                    url=settings.upstash_redis_url,
                    token=settings.upstash_redis_token,
                )
            except Exception:
                return None
    return _client


async def cache_get(key: str) -> Any | None:
    """
    Get a value from cache.

    Returns None if key doesn't exist or Redis is unavailable.
    """
    try:
        client = get_redis()
        if client is None:
            return None
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """
    Set a value in cache with a TTL.

    Args:
        key: Cache key
        value: Any JSON-serializable value
        ttl_seconds: Time to live in seconds (default 5 minutes)
    """
    try:
        client = get_redis()
        if client is None:
            return
        client.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception:
        pass  # Cache failures should never crash the app


async def cache_delete(key: str) -> None:
    """Delete a key from cache."""
    try:
        client = get_redis()
        if client is None:
            return
        client.delete(key)
    except Exception:
        pass


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern (e.g., 'mastery:project_123:*')."""
    try:
        client = get_redis()
        if client is None:
            return
        # Upstash doesn't support SCAN, so we use pattern-based delete
        # For production, consider using a more specific key structure
        keys = client.keys(pattern)
        if keys:
            for key in keys:
                client.delete(key)
    except Exception:
        pass


async def check_rate_limit(user_id: str, endpoint: str) -> bool:
    """
    Check if a user has exceeded the rate limit for an endpoint.

    Returns True if the request is allowed, False if rate limited.

    Uses a sliding window counter in Redis.
    """
    settings = get_settings()
    try:
        client = get_redis()
        if client is None:
            return True  # Allow all requests if Redis is unavailable

        key = f"rate_limit:{user_id}:{endpoint}"
        current = client.get(key)

        if current is None:
            client.set(key, "1", ex=settings.rate_limit_window)
            return True

        count = int(current)
        if count >= settings.rate_limit_requests:
            return False

        client.incr(key)
        return True
    except Exception:
        return True  # Allow on Redis error


def make_cache_key(*parts: str) -> str:
    """
    Create a consistent cache key from multiple parts.

    Example: make_cache_key("mastery", project_id, user_id) → "mastery:abc123:def456"
    """
    return ":".join(str(p) for p in parts)


def hash_for_cache(content: str) -> str:
    """Create a short hash for cache key generation."""
    return hashlib.md5(content.encode()).hexdigest()[:12]
