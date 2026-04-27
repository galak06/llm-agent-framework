from __future__ import annotations

import pytest

from src.core.config import Settings
from src.memory.embedding_client import (
    HashEmbeddingClient,
    VoyageEmbeddingClient,
    create_embedding_client,
)
from src.memory.vector_store import EMBEDDING_DIM


class TestHashEmbeddingClient:
    """Tests for the deterministic hash-based embedder used as a no-API-key fallback."""

    @pytest.mark.asyncio
    async def test_returns_correct_dimension(self) -> None:
        client = HashEmbeddingClient(dim=EMBEDDING_DIM)
        [vec] = await client.embed(['hello world'])
        assert len(vec) == EMBEDDING_DIM

    @pytest.mark.asyncio
    async def test_values_in_range(self) -> None:
        client = HashEmbeddingClient(dim=EMBEDDING_DIM)
        [vec] = await client.embed(['test input'])
        assert all(-1 <= v <= 1 for v in vec)

    @pytest.mark.asyncio
    async def test_deterministic(self) -> None:
        client = HashEmbeddingClient(dim=EMBEDDING_DIM)
        [vec1] = await client.embed(['same text'])
        [vec2] = await client.embed(['same text'])
        assert vec1 == vec2

    @pytest.mark.asyncio
    async def test_different_text_different_vectors(self) -> None:
        client = HashEmbeddingClient(dim=EMBEDDING_DIM)
        [vec1] = await client.embed(['chocolate'])
        [vec2] = await client.embed(['chicken'])
        assert vec1 != vec2

    @pytest.mark.asyncio
    async def test_case_insensitive(self) -> None:
        client = HashEmbeddingClient(dim=EMBEDDING_DIM)
        [vec1] = await client.embed(['Hello World'])
        [vec2] = await client.embed(['hello world'])
        assert vec1 == vec2

    @pytest.mark.asyncio
    async def test_strips_whitespace(self) -> None:
        client = HashEmbeddingClient(dim=EMBEDDING_DIM)
        [vec1] = await client.embed(['  hello  '])
        [vec2] = await client.embed(['hello'])
        assert vec1 == vec2

    @pytest.mark.asyncio
    async def test_custom_dimension(self) -> None:
        client = HashEmbeddingClient(dim=64)
        [vec] = await client.embed(['test'])
        assert len(vec) == 64

    @pytest.mark.asyncio
    async def test_batch_returns_one_per_text(self) -> None:
        client = HashEmbeddingClient(dim=EMBEDDING_DIM)
        vecs = await client.embed(['a', 'b', 'c'])
        assert len(vecs) == 3
        assert vecs[0] != vecs[1] != vecs[2]

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        client = HashEmbeddingClient(dim=EMBEDDING_DIM)
        vecs = await client.embed([])
        assert vecs == []


class TestCreateEmbeddingClient:
    """Factory picks Voyage when key is present, hash fallback otherwise."""

    def test_no_key_returns_hash_client(self, settings: Settings) -> None:
        client = create_embedding_client(settings)
        assert isinstance(client, HashEmbeddingClient)
        assert client.dim == settings.voyage_embedding_dim

    def test_with_key_returns_voyage_client(self, settings: Settings) -> None:
        from pydantic import SecretStr

        settings_with_key = settings.model_copy(
            update={'voyage_api_key': SecretStr('pa-test-key')}
        )
        client = create_embedding_client(settings_with_key)
        assert isinstance(client, VoyageEmbeddingClient)
        assert client.dim == settings_with_key.voyage_embedding_dim
