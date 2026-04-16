from __future__ import annotations

import time

import redis.asyncio as redis
import structlog
from fastapi import APIRouter

from src.core.dependencies import ContainerDep
from src.domain.schemas import HealthResponse, ServiceStatus

logger = structlog.get_logger()
router = APIRouter()

_start_time = time.time()


@router.get('/health', response_model=HealthResponse)
async def health_check(container: ContainerDep) -> HealthResponse:
    """Deep health check — verifies all dependencies."""
    checks: dict[str, ServiceStatus] = {}

    # Redis check
    try:
        r = redis.from_url(container.settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
        await r.ping()
        checks['redis'] = ServiceStatus.OK
        await r.aclose()
    except Exception:
        checks['redis'] = ServiceStatus.DOWN

    # Database check
    try:
        from sqlalchemy import text

        async with container.engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        checks['database'] = ServiceStatus.OK
    except Exception:
        checks['database'] = ServiceStatus.DOWN

    # Celery check
    try:
        from src.jobs.worker import celery_app

        inspect = celery_app.control.inspect(timeout=2.0)
        ping_result = inspect.ping()
        checks['celery'] = ServiceStatus.OK if ping_result else ServiceStatus.DOWN
    except Exception:
        checks['celery'] = ServiceStatus.DOWN

    overall = (
        ServiceStatus.OK
        if all(v == ServiceStatus.OK for v in checks.values())
        else ServiceStatus.DEGRADED
    )

    return HealthResponse(
        status=overall,
        version='1.0.0',
        uptime_seconds=time.time() - _start_time,
        checks=checks,
    )
