"""Origin header allowlist enforcement.

CORS only blocks cross-origin requests from browsers — non-browser clients
(curl, python requests, scrapers) ignore it. This guard runs server-side and
rejects requests whose ``Origin`` header is not in the configured allowlist.

When the allowlist is empty the guard is a no-op (dev default). When populated,
any request with a missing or non-matching ``Origin`` header is rejected with 403.
"""

from __future__ import annotations

import structlog
from fastapi import HTTPException, Request, status

from src.core.dependencies import ContainerDep

logger = structlog.get_logger()


async def require_allowed_origin(request: Request, container: ContainerDep) -> None:
    """FastAPI dependency that enforces the widget origin allowlist."""
    allowed = container.settings.widget_allowed_origins
    if not allowed:
        return

    origin = request.headers.get('origin')
    if origin not in allowed:
        logger.warning('origin_guard.rejected', origin=origin, path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Origin not allowed',
        )
