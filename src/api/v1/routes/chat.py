from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.api.v1.middleware.api_key import require_widget_key
from src.core.dependencies import ContainerDep
from src.core.security import sanitize_input
from src.domain.schemas import AskRequest, AskResponse, RunStatus, RunStatusResponse

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    '/ask',
    response_model=AskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_widget_key)],
)
async def ask(request: AskRequest, container: ContainerDep) -> AskResponse:
    """Submit a question — returns run_id for polling."""
    sanitized = sanitize_input(request.message, container.settings)

    run_id = str(uuid.uuid4())

    # Set initial PENDING status
    await container.result_store.set_status(run_id, RunStatus.PENDING)

    # Enqueue Celery task
    from src.jobs.tasks import run_agent_task

    run_agent_task.delay(
        request.model_dump() | {'message': sanitized},
        run_id,
    )

    logger.info('ask.enqueued', run_id=run_id, user_id=request.user_id)

    return AskResponse(
        run_id=run_id,
        status_url=f'/api/{container.settings.api_version}/runs/{run_id}',
    )


@router.get(
    '/runs/{run_id}',
    response_model=RunStatusResponse,
    dependencies=[Depends(require_widget_key)],
)
async def get_run_status(
    run_id: Annotated[
        str,
        Path(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'),
    ],
    container: ContainerDep,
) -> RunStatusResponse:
    """Poll for agent run status and result."""
    result = await container.result_store.get(run_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Run not found: {run_id}',
        )
    return result
