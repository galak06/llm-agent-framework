"""Integration tests for RunResultStore round-trip via Redis."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest

from src.core.config import Settings
from src.domain.schemas import RunStatus, RunStatusResponse
from src.jobs.result_store import RunResultStore


def redis_available() -> bool:
    try:
        import redis

        url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(url)
        r.ping()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not redis_available(), reason='Redis not available')
class TestRunResultStore:
    @pytest.fixture
    def store(self, settings: Settings) -> RunResultStore:
        return RunResultStore(settings)

    @pytest.mark.asyncio
    async def test_set_and_get_status(self, store: RunResultStore) -> None:
        await store.set_status('run-test-1', RunStatus.PENDING)
        result = await store.get('run-test-1')
        assert result is not None
        assert result.status == RunStatus.PENDING
        assert result.run_id == 'run-test-1'

    @pytest.mark.asyncio
    async def test_status_transitions(self, store: RunResultStore) -> None:
        await store.set_status('run-test-2', RunStatus.PENDING)
        await store.set_status('run-test-2', RunStatus.RUNNING)
        result = await store.get('run-test-2')
        assert result is not None
        assert result.status == RunStatus.RUNNING

    @pytest.mark.asyncio
    async def test_set_full_result(self, store: RunResultStore) -> None:
        now = datetime.now(UTC)
        response = RunStatusResponse(
            run_id='run-test-3',
            status=RunStatus.DONE,
            answer='Rice is safe for dogs.',
            tools_used=[],
            total_tokens=120,
            created_at=now,
        )
        await store.set_result('run-test-3', response)
        result = await store.get('run-test-3')
        assert result is not None
        assert result.status == RunStatus.DONE
        assert result.answer == 'Rice is safe for dogs.'
        assert result.total_tokens == 120

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, store: RunResultStore) -> None:
        result = await store.get('nonexistent-run-id')
        assert result is None

    @pytest.mark.asyncio
    async def test_failed_status_has_completed_at(self, store: RunResultStore) -> None:
        await store.set_status('run-test-4', RunStatus.PENDING)
        await store.set_status('run-test-4', RunStatus.FAILED)
        result = await store.get('run-test-4')
        assert result is not None
        assert result.status == RunStatus.FAILED
        assert result.completed_at is not None
