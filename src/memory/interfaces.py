from __future__ import annotations

from typing import Protocol

from src.domain.schemas import Message


class MemoryReader(Protocol):
    """Read conversation history or semantic memory."""

    async def get_history(self, session_id: str, limit: int = 10) -> list[Message]: ...

    async def search(self, query: str, top_k: int = 3) -> list[Message]: ...


class MemoryWriter(Protocol):
    """Write conversation messages to memory."""

    async def add(self, session_id: str, message: Message) -> None: ...

    async def clear(self, session_id: str) -> None: ...
