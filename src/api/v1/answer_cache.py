"""Response cache for stateless anonymous questions.

Short-circuits repeated identical questions (text and/or image) that arrive
without a ``chatId`` — the common cost-burn vector where a bot repeatedly
sends the same prompt or uploads the same ingredient label with a rotating
anonymous session. The key includes an optional image-content hash so the
same photo uploaded twice reuses the prior analysis instead of re-paying for
Gemini vision. Only kicks in when there's no session identity, so multi-turn
personalized conversations are never affected.
"""

from __future__ import annotations

import hashlib

import redis.asyncio as redis
import structlog

from src.core.config import Settings
from src.core.redis_keys import prefixed_key

logger = structlog.get_logger()


class AnswerCache:
    """Normalized-question → answer cache backed by Redis with TTL."""

    def __init__(self, settings: Settings) -> None:
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
        self._ttl = settings.answer_cache_ttl_seconds
        self._enabled = settings.answer_cache_enabled
        self._prefix = settings.redis_key_prefix

    @staticmethod
    def _key(prefix: str, chatflow_id: str, question: str, image_hash: str = '') -> str:
        normalized = question.lower().strip()
        source = f'{normalized}|{image_hash}' if image_hash else normalized
        digest = hashlib.sha256(source.encode('utf-8')).hexdigest()[:32]
        return prefixed_key(prefix, 'answer_cache', chatflow_id, digest)

    @staticmethod
    def hash_images(images_data: list[bytes]) -> str:
        """Return a compact digest of ordered image bytes for use as a cache key."""
        if not images_data:
            return ''
        h = hashlib.sha256()
        for data in images_data:
            h.update(len(data).to_bytes(8, 'big'))
            h.update(data)
        return h.hexdigest()[:32]

    async def get(self, chatflow_id: str, question: str, image_hash: str = '') -> str | None:
        if not self._enabled:
            return None
        key = self._key(self._prefix, chatflow_id, question, image_hash)
        return await self._redis.get(key)  # type: ignore[no-any-return]

    async def set(
        self, chatflow_id: str, question: str, answer: str, image_hash: str = ''
    ) -> None:
        if not self._enabled:
            return
        key = self._key(self._prefix, chatflow_id, question, image_hash)
        await self._redis.setex(key, self._ttl, answer)
