"""
Solar Operations OS — Idempotency Key Store
Prevents duplicate execution of mutating operations.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings

# TTL for idempotency keys: 24 hours
_IDEMPOTENCY_TTL_SECONDS = 86400
_KEY_PREFIX = "idempotency"


def _make_redis_key(org_id: uuid.UUID, idempotency_key: str) -> str:
    """
    Build a Redis key scoped to the organization.
    This prevents cross-tenant idempotency key collisions.
    """
    return f"{_KEY_PREFIX}:{org_id}:{idempotency_key}"


def _hash_payload(payload: dict[str, Any]) -> str:
    """Deterministic hash of the request payload for conflict detection."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


class IdempotencyStore:
    def __init__(self, redis_client: aioredis.Redis) -> None:  # type: ignore[type-arg]
        self._redis = redis_client

    async def check_and_lock(
        self,
        org_id: uuid.UUID,
        idempotency_key: str,
        payload_hash: str,
    ) -> tuple[bool, dict[str, Any] | None]:
        """
        Check if this idempotency key has been used before.

        Returns:
            (is_replay, cached_response) where:
            - is_replay=False, cached_response=None → first use, proceed
            - is_replay=True, cached_response=dict → replay the cached response
            - Raises IdempotencyConflictError if same key with different payload
        """
        from app.core.errors import IdempotencyConflictError

        redis_key = _make_redis_key(org_id, idempotency_key)
        existing = await self._redis.get(redis_key)

        if existing is not None:
            data = json.loads(existing)
            if data["payload_hash"] != payload_hash:
                raise IdempotencyConflictError(
                    "Idempotency key was used with a different request payload"
                )
            if data.get("response") is not None:
                return True, data["response"]
            # Key exists but response not yet stored → in-flight, wait
            return True, None

        # First use — store lock with pending state
        lock_data = json.dumps({"payload_hash": payload_hash, "response": None})
        # NX = only set if not exists (prevents race)
        set_result = await self._redis.set(
            redis_key, lock_data, ex=_IDEMPOTENCY_TTL_SECONDS, nx=True
        )
        if set_result is None:
            # Another request won the race — re-read
            return await self.check_and_lock(org_id, idempotency_key, payload_hash)

        return False, None

    async def store_response(
        self,
        org_id: uuid.UUID,
        idempotency_key: str,
        payload_hash: str,
        response: dict[str, Any],
    ) -> None:
        """Store the successful response for future replays."""
        redis_key = _make_redis_key(org_id, idempotency_key)
        data = json.dumps({"payload_hash": payload_hash, "response": response})
        await self._redis.set(redis_key, data, ex=_IDEMPOTENCY_TTL_SECONDS)


# ── Redis Client Singleton ────────────────────────────────────────────────────
_redis_client: aioredis.Redis | None = None  # type: ignore[type-arg]


def get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client


async def init_redis() -> None:
    global _redis_client
    settings = get_settings()
    _redis_client = await aioredis.from_url(
        str(settings.REDIS_URL),
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,
    )


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
