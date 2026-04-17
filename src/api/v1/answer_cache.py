"""Response cache for stateless anonymous questions.

Short-circuits repeated identical questions that arrive without a ``chatId`` —
the common cost-burn vector where a bot repeatedly asks "is chocolate safe?"
with a rotating anonymous session. Only kicks in when there's no session
identity and no image uploads, so it never interferes with multi-turn
personalized conversations.
"""

from __future__ import annotations

import hashlib

import redis.asyncio as redis
import structlog

from src.core.config import Settings

logger = structlog.get_logger()


class AnswerCache:
    """Normalized-question → answer cache backed by Redis with TTL."""

    def __init__(self, settings: Settings) -> None:
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
        self._ttl = settings.answer_cache_ttl_seconds
        self._enabled = settings.answer_cache_enabled

    @staticmethod
    def _key(chatflow_id: str, question: str) -> str:
        normalized = question.lower().strip()
        digest = hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:32]
        return f'answer_cache:{chatflow_id}:{digest}'

    async def get(self, chatflow_id: str, question: str) -> str | None:
        if not self._enabled:
            return None
        return await self._redis.get(self._key(chatflow_id, question))  # type: ignore[no-any-return]

    async def set(self, chatflow_id: str, question: str, answer: str) -> None:
        if not self._enabled:
            return
        await self._redis.setex(self._key(chatflow_id, question), self._ttl, answer)
