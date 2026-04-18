"""Ephemeral Redis store for uploaded image bytes.

flowise-embed renders message thumbnails by fetching
``GET /api/v1/get-upload-file?chatflowId=X&chatId=Y&fileName=Z``. We don't
persist uploads long-term (images go straight to the LLM), so we cache the
raw bytes here for the session TTL and serve them back on demand.
"""

from __future__ import annotations

import redis.asyncio as redis
import structlog

from src.core.config import Settings
from src.core.redis_keys import prefixed_key

logger = structlog.get_logger()


class UploadStore:
    """Short-lived image cache so the widget can render uploaded thumbnails."""

    def __init__(self, settings: Settings) -> None:
        self._redis = redis.from_url(settings.redis_url)  # type: ignore[no-untyped-call]
        self._ttl = settings.session_ttl_seconds
        self._prefix = settings.redis_key_prefix

    def _key(self, chatflow_id: str, chat_id: str, file_name: str) -> str:
        return prefixed_key(self._prefix, 'upload', chatflow_id, chat_id, file_name)

    async def put(
        self, chatflow_id: str, chat_id: str, file_name: str, mime: str, data: bytes
    ) -> None:
        key = self._key(chatflow_id, chat_id, file_name)
        await self._redis.hset(key, mapping={'mime': mime, 'data': data})
        await self._redis.expire(key, self._ttl)
        logger.info(
            'upload_store.put',
            chatflow_id=chatflow_id,
            file_name=file_name,
            bytes=len(data),
        )

    async def get(
        self, chatflow_id: str, chat_id: str, file_name: str
    ) -> tuple[str, bytes] | None:
        key = self._key(chatflow_id, chat_id, file_name)
        raw = await self._redis.hgetall(key)
        if not raw:
            return None
        mime = raw.get(b'mime', b'application/octet-stream').decode('utf-8', errors='replace')
        data = raw.get(b'data', b'')
        return mime, data
