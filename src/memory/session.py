from __future__ import annotations

import redis.asyncio as redis
import structlog

from src.core.config import Settings
from src.domain.schemas import Message

logger = structlog.get_logger()


class RedisSessionMemory:
    """Short-term session memory backed by Redis with TTL."""

    def __init__(self, settings: Settings) -> None:
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
        self._ttl = settings.session_ttl_seconds

    def _key(self, session_id: str) -> str:
        return f'session:{session_id}:messages'

    async def get_history(self, session_id: str, limit: int = 10) -> list[Message]:
        key = self._key(session_id)
        raw = await self._redis.lrange(key, -limit, -1)
        return [Message.model_validate_json(item) for item in raw]

    async def add(self, session_id: str, message: Message) -> None:
        key = self._key(session_id)
        await self._redis.rpush(key, message.model_dump_json())
        await self._redis.expire(key, self._ttl)
        logger.info('memory.session.add', session_id=session_id, role=message.role)

    async def clear(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))
        logger.info('memory.session.clear', session_id=session_id)

    async def search(self, query: str, top_k: int = 3) -> list[Message]:
        """Session memory does not support semantic search."""
        return []
