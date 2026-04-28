from __future__ import annotations

from datetime import UTC, datetime

import structlog
from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import Column, DateTime, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.models import Base
from src.domain.schemas import Message, Role
from src.memory.embedding_client import EmbeddingClient

logger = structlog.get_logger()

EMBEDDING_DIM = 1024


class MemoryEmbedding(Base):
    """Stores conversation messages with vector embeddings for semantic search."""

    __tablename__ = 'memory_embeddings'

    id = Column(String(36), primary_key=True)
    session_id = Column(String(255), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class PgVectorMemory:
    """Long-term semantic memory backed by pgvector."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedding_client: EmbeddingClient,
    ) -> None:
        self._session_factory = session_factory
        self._embedder = embedding_client

    async def get_history(self, session_id: str, limit: int = 10) -> list[Message]:
        """Retrieve recent messages for a session, ordered by time."""
        async with self._session_factory() as session:
            stmt = (
                select(MemoryEmbedding)
                .where(MemoryEmbedding.session_id == session_id)
                .order_by(MemoryEmbedding.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = list(result.scalars().all())
            rows.reverse()
            return [
                Message(
                    id=row.id,
                    role=Role(str(row.role)),
                    content=row.content,
                )
                for row in rows
            ]

    async def add(self, session_id: str, message: Message) -> None:
        """Store a message with its embedding."""
        [embedding] = await self._embedder.embed([message.content], input_type='document')

        record = MemoryEmbedding(
            id=message.id,
            session_id=session_id,
            role=message.role.value,
            content=message.content,
            embedding=embedding,
        )

        async with self._session_factory() as session:
            session.add(record)
            await session.commit()

        logger.info(
            'memory.vector.add',
            session_id=session_id,
            role=message.role,
            message_id=message.id,
        )

    async def clear(self, session_id: str) -> None:
        """Delete all messages for a session."""
        async with self._session_factory() as session:
            stmt = delete(MemoryEmbedding).where(MemoryEmbedding.session_id == session_id)
            await session.execute(stmt)
            await session.commit()

        logger.info('memory.vector.clear', session_id=session_id)

    async def search(self, query: str, top_k: int = 3) -> list[Message]:
        """Find the most semantically similar messages using cosine distance."""
        [query_embedding] = await self._embedder.embed([query], input_type='query')

        async with self._session_factory() as session:
            stmt = (
                select(MemoryEmbedding)
                .order_by(MemoryEmbedding.embedding.cosine_distance(query_embedding))
                .limit(top_k)
            )
            result = await session.execute(stmt)
            rows = list(result.scalars().all())
            return [
                Message(
                    id=row.id,
                    role=Role(str(row.role)),
                    content=row.content,
                )
                for row in rows
            ]
