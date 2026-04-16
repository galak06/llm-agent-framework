from __future__ import annotations

import time

import redis.asyncio as redis
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.core.config import Settings

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter backed by Redis."""

    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._max_requests = settings.rate_limit_requests
        self._window = settings.rate_limit_window_seconds

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        if request.url.path.endswith('/health'):
            return await call_next(request)

        client_ip = request.client.host if request.client else 'unknown'
        key = f'rate_limit:{client_ip}'
        now = time.time()

        pipe = self._redis.pipeline()
        await pipe.zremrangebyscore(key, 0, now - self._window)
        await pipe.zadd(key, {str(now): now})
        await pipe.zcard(key)
        await pipe.expire(key, self._window)
        results = await pipe.execute()

        request_count = results[2]
        if request_count > self._max_requests:
            logger.warning('rate_limit.exceeded', client_ip=client_ip, count=request_count)
            return JSONResponse(
                status_code=429,
                content={'detail': 'Rate limit exceeded'},
            )

        return await call_next(request)
