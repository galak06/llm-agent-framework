"""Integration tests for Redis session memory round-trip."""

from __future__ import annotations

import os

import pytest

from src.core.config import Settings
from src.domain.schemas import Message, Role
from src.memory.session import RedisSessionMemory


def redis_available() -> bool:
    """Check if Redis is reachable for integration tests."""
    try:
        import redis

        url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(url)
        r.ping()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not redis_available(), reason='Redis not available')
class TestRedisSessionMemory:
    @pytest.fixture
    def memory(self, settings: Settings) -> RedisSessionMemory:
        return RedisSessionMemory(settings)

    @pytest.fixture(autouse=True)
    async def cleanup(self, memory: RedisSessionMemory) -> None:
        await memory.clear('test-session')
        yield  # type: ignore[misc]
        await memory.clear('test-session')

    @pytest.mark.asyncio
    async def test_add_and_get_history(self, memory: RedisSessionMemory) -> None:
        await memory.add('test-session', Message(role=Role.USER, content='hello'))
        await memory.add('test-session', Message(role=Role.ASSISTANT, content='hi there'))

        history = await memory.get_history('test-session')
        assert len(history) == 2
        assert history[0].role == Role.USER
        assert history[0].content == 'hello'
        assert history[1].role == Role.ASSISTANT
        assert history[1].content == 'hi there'

    @pytest.mark.asyncio
    async def test_history_respects_limit(self, memory: RedisSessionMemory) -> None:
        for i in range(5):
            await memory.add('test-session', Message(role=Role.USER, content=f'msg {i}'))

        history = await memory.get_history('test-session', limit=3)
        assert len(history) == 3
        assert history[0].content == 'msg 2'
        assert history[2].content == 'msg 4'

    @pytest.mark.asyncio
    async def test_clear_removes_all(self, memory: RedisSessionMemory) -> None:
        await memory.add('test-session', Message(role=Role.USER, content='temp'))
        await memory.clear('test-session')

        history = await memory.get_history('test-session')
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_search_returns_empty(self, memory: RedisSessionMemory) -> None:
        result = await memory.search('anything')
        assert result == []

    @pytest.mark.asyncio
    async def test_separate_sessions(self, memory: RedisSessionMemory) -> None:
        await memory.add('session-a', Message(role=Role.USER, content='from a'))
        await memory.add('session-b', Message(role=Role.USER, content='from b'))

        history_a = await memory.get_history('session-a')
        history_b = await memory.get_history('session-b')

        assert len(history_a) == 1
        assert history_a[0].content == 'from a'
        assert len(history_b) == 1
        assert history_b[0].content == 'from b'

        # Cleanup
        await memory.clear('session-a')
        await memory.clear('session-b')
