from __future__ import annotations

import json
from datetime import UTC, datetime

import redis.asyncio as redis
import structlog

from src.core.config import Settings
from src.core.redis_keys import prefixed_key
from src.domain.schemas import RunStatus, RunStatusResponse

logger = structlog.get_logger()


class RunResultStore:
    """Redis-backed store for agent run status and results."""

    def __init__(self, settings: Settings) -> None:
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
        self._ttl = settings.run_result_ttl_seconds
        self._prefix = settings.redis_key_prefix

    def _key(self, run_id: str) -> str:
        return prefixed_key(self._prefix, 'runs', run_id)

    async def set_status(self, run_id: str, status: RunStatus) -> None:
        key = self._key(run_id)
        existing = await self._redis.get(key)
        if existing is not None:
            data = json.loads(existing)
            data['status'] = status.value
            if status == RunStatus.DONE or status == RunStatus.FAILED:
                data['completed_at'] = datetime.now(UTC).isoformat()
        else:
            data = {
                'run_id': run_id,
                'status': status.value,
                'created_at': datetime.now(UTC).isoformat(),
            }
        await self._redis.set(key, json.dumps(data), ex=self._ttl)
        logger.info('result_store.set_status', run_id=run_id, status=status.value)

    async def set_result(self, run_id: str, result: RunStatusResponse) -> None:
        key = self._key(run_id)
        await self._redis.set(key, result.model_dump_json(), ex=self._ttl)
        logger.info('result_store.set_result', run_id=run_id)

    async def get(self, run_id: str) -> RunStatusResponse | None:
        key = self._key(run_id)
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return RunStatusResponse.model_validate_json(raw)
