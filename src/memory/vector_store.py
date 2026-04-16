from __future__ import annotations

import structlog

from src.core.config import Settings
from src.domain.schemas import Message

logger = structlog.get_logger()


class PgVectorMemory:
    """Long-term semantic memory backed by pgvector in Supabase."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def get_history(self, session_id: str, limit: int = 10) -> list[Message]:
        raise NotImplementedError

    async def add(self, session_id: str, message: Message) -> None:
        raise NotImplementedError

    async def clear(self, session_id: str) -> None:
        raise NotImplementedError

    async def search(self, query: str, top_k: int = 3) -> list[Message]:
        raise NotImplementedError
