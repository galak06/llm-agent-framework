"""Embedding clients — turn text into vectors for pgvector storage and search.

Two implementations:
- VoyageEmbeddingClient: production. Calls Voyage AI's HTTP API.
- HashEmbeddingClient: deterministic SHA-based pseudo-embeddings. Used as a
  fallback when no API key is configured (tests, local dev). Supports exact-
  and near-duplicate matching only — never semantic similarity.
"""

from __future__ import annotations

import hashlib
import struct
from typing import Any, Literal, Protocol, cast

import structlog

from src.core.config import Settings

logger = structlog.get_logger()

InputType = Literal['document', 'query']


class EmbeddingClient(Protocol):
    """Async embedding interface. ``input_type`` lets providers like Voyage
    route documents and queries through different projections for better recall.
    """

    dim: int

    async def embed(
        self, texts: list[str], input_type: InputType = 'document'
    ) -> list[list[float]]: ...


class HashEmbeddingClient:
    """Deterministic SHA-based pseudo-embeddings. No semantic meaning."""

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim

    async def embed(
        self, texts: list[str], input_type: InputType = 'document'
    ) -> list[list[float]]:
        return [self._hash(t) for t in texts]

    def _hash(self, text: str) -> list[float]:
        normalized = text.lower().strip()
        values: list[float] = []
        for i in range(self.dim):
            h = hashlib.sha256(f'{i}:{normalized}'.encode()).digest()
            raw = struct.unpack('<I', h[:4])[0]
            values.append((raw / 0xFFFFFFFF) * 2 - 1)
        return values


class VoyageEmbeddingClient:
    """Voyage AI embeddings. Uses the official ``voyageai`` async client."""

    def __init__(self, api_key: str, model: str, dim: int) -> None:
        # Imported lazily so test envs without voyageai installed still work
        # via HashEmbeddingClient.
        import voyageai

        self._client: Any = voyageai.AsyncClient(api_key=api_key)  # type: ignore[attr-defined]
        self._model = model
        self.dim = dim

    async def embed(
        self, texts: list[str], input_type: InputType = 'document'
    ) -> list[list[float]]:
        if not texts:
            return []
        result = await self._client.embed(
            texts=texts,
            model=self._model,
            input_type=input_type,
        )
        embeddings = cast(list[list[float]], result.embeddings)
        logger.info(
            'embedding.voyage',
            model=self._model,
            count=len(texts),
            input_type=input_type,
            total_tokens=getattr(result, 'total_tokens', None),
        )
        return embeddings


def create_embedding_client(settings: Settings) -> EmbeddingClient:
    """Build the right embedder based on whether a Voyage API key is configured."""
    api_key = settings.voyage_api_key.get_secret_value()
    if api_key:
        return VoyageEmbeddingClient(
            api_key=api_key,
            model=settings.voyage_model,
            dim=settings.voyage_embedding_dim,
        )
    logger.warning(
        'embedding.fallback_to_hash',
        reason='VOYAGE_API_KEY not set — using deterministic hash embedder',
        dim=settings.voyage_embedding_dim,
    )
    return HashEmbeddingClient(dim=settings.voyage_embedding_dim)
