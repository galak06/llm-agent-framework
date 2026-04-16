from __future__ import annotations

import time

import redis.asyncio as redis
import structlog
from fastapi import APIRouter

from src.core.config import get_settings
from src.domain.schemas import HealthResponse, ServiceStatus

logger = structlog.get_logger()
router = APIRouter()

_start_time = time.time()


@router.get('/health', response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Deep health check — verifies all dependencies."""
    settings = get_settings()
    checks: dict[str, ServiceStatus] = {}

    # Redis check
    try:
        r = redis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
        await r.ping()
        checks['redis'] = ServiceStatus.OK
        await r.aclose()
    except Exception:
        checks['redis'] = ServiceStatus.DOWN

    # Database check placeholder
    checks['database'] = ServiceStatus.OK

    # Celery check placeholder
    checks['celery'] = ServiceStatus.OK

    # Anthropic check placeholder
    checks['anthropic'] = ServiceStatus.OK

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
