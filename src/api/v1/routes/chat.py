from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.middleware.api_key import require_widget_key
from src.core.config import get_settings
from src.core.security import sanitize_input
from src.domain.schemas import AskRequest, AskResponse, RunStatus, RunStatusResponse
from src.jobs.result_store import RunResultStore

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    '/ask',
    response_model=AskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_widget_key)],
)
async def ask(request: AskRequest) -> AskResponse:
    """Submit a question — returns run_id for polling."""
    settings = get_settings()
    sanitized = sanitize_input(request.message, settings)

    run_id = str(uuid.uuid4())

    # Set initial PENDING status
    store = RunResultStore(settings)
    await store.set_status(run_id, RunStatus.PENDING)

    # Enqueue Celery task
    from src.jobs.tasks import run_agent_task

    run_agent_task.delay(
        request.model_dump() | {'message': sanitized},
        run_id,
    )

    logger.info('ask.enqueued', run_id=run_id, user_id=request.user_id)

    return AskResponse(
        run_id=run_id,
        status_url=f'/api/{settings.api_version}/runs/{run_id}',
    )


@router.get(
    '/runs/{run_id}',
    response_model=RunStatusResponse,
    dependencies=[Depends(require_widget_key)],
)
async def get_run_status(run_id: str) -> RunStatusResponse:
    """Poll for agent run status and result."""
    settings = get_settings()
    store = RunResultStore(settings)
    result = await store.get(run_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Run not found: {run_id}',
        )
    return result
