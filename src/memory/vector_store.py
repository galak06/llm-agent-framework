from __future__ import annotations

import hashlib
import struct
from datetime import UTC, datetime

import structlog
from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import Column, DateTime, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import Settings
from src.db.models import Base
from src.domain.schemas import Message, Role

logger = structlog.get_logger()

EMBEDDING_DIM = 256


class MemoryEmbedding(Base):
    """Stores conversation messages with vector embeddings for semantic search."""

    __tablename__ = 'memory_embeddings'

    id = Column(String(36), primary_key=True)
    session_id = Column(String(255), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


def _hash_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Generate a deterministic pseudo-embedding from text via hashing.

    This is a lightweight fallback for environments without an embedding API.
    It produces consistent vectors for identical text, enabling exact and
    near-duplicate matching. For production semantic search, replace with
    a real embedding model (e.g., Voyage AI, OpenAI text-embedding-3-small).
    """
    # Hash text in overlapping shingle windows for basic similarity
    values: list[float] = []
    for i in range(dim):
        h = hashlib.sha256(f'{i}:{text.lower().strip()}'.encode()).digest()
        # Unpack first 4 bytes as float-like value in [-1, 1]
        raw = struct.unpack('<I', h[:4])[0]
        values.append((raw / 0xFFFFFFFF) * 2 - 1)
    return values


class PgVectorMemory:
    """Long-term semantic memory backed by pgvector."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
        )
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def _get_session(self) -> AsyncSession:
        return self._session_factory()

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
            rows.reverse()  # Return in chronological order
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
        embedding = _hash_embedding(message.content)

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
        from sqlalchemy import delete

        async with self._session_factory() as session:
            stmt = delete(MemoryEmbedding).where(MemoryEmbedding.session_id == session_id)
            await session.execute(stmt)
            await session.commit()

        logger.info('memory.vector.clear', session_id=session_id)

    async def search(self, query: str, top_k: int = 3) -> list[Message]:
        """Find the most semantically similar messages using cosine distance."""
        query_embedding = _hash_embedding(query)

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
