"""Per-chatId sliding-window rate limiter.

Complements the per-IP middleware so a single browser (identified by its
flowise-embed ``chatId``) can't monopolize the LLM budget even when many users
share the same NAT or CDN egress IP.
"""

from __future__ import annotations

import time

import redis.asyncio as redis
import structlog
from fastapi import HTTPException, status

from src.core.config import Settings
from src.core.redis_keys import prefixed_key

logger = structlog.get_logger()


class ChatRateLimiter:
    """Sliding-window per-chatId limiter backed by Redis sorted sets."""

    def __init__(self, settings: Settings) -> None:
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
        self._max_messages = settings.chat_messages_per_hour
        self._window = settings.chat_rate_limit_window_seconds
        self._prefix = settings.redis_key_prefix

    async def check(self, chat_id: str) -> None:
        """Record the current request for ``chat_id`` and raise 429 if over the cap."""
        key = prefixed_key(self._prefix, 'chat_limit', chat_id)
        now = time.time()

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - self._window)
        pipe.zadd(key, {f'{now}': now})
        pipe.zcard(key)
        pipe.expire(key, self._window)
        results = await pipe.execute()

        count: int = results[2]
        if count > self._max_messages:
            logger.warning('chat_limit.exceeded', chat_id=chat_id, count=count)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f'Too many messages in the last hour (max {self._max_messages})',
            )
