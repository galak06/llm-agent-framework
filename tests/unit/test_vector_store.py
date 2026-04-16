from __future__ import annotations

from src.memory.vector_store import EMBEDDING_DIM, _hash_embedding


class TestHashEmbedding:
    """Tests for the fallback hash-based embedding function."""

    def test_returns_correct_dimension(self) -> None:
        vec = _hash_embedding('hello world')
        assert len(vec) == EMBEDDING_DIM

    def test_values_in_range(self) -> None:
        vec = _hash_embedding('test input')
        assert all(-1 <= v <= 1 for v in vec)

    def test_deterministic(self) -> None:
        vec1 = _hash_embedding('same text')
        vec2 = _hash_embedding('same text')
        assert vec1 == vec2

    def test_different_text_different_vectors(self) -> None:
        vec1 = _hash_embedding('chocolate')
        vec2 = _hash_embedding('chicken')
        assert vec1 != vec2

    def test_case_insensitive(self) -> None:
        vec1 = _hash_embedding('Hello World')
        vec2 = _hash_embedding('hello world')
        assert vec1 == vec2

    def test_strips_whitespace(self) -> None:
        vec1 = _hash_embedding('  hello  ')
        vec2 = _hash_embedding('hello')
        assert vec1 == vec2

    def test_custom_dimension(self) -> None:
        vec = _hash_embedding('test', dim=64)
        assert len(vec) == 64
