"""Flowise-compatible prediction endpoint.

Accepts POST /api/v1/prediction/{chatflowid} with {"question": "..."}
and returns {"text": "..."} synchronously.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.core.dependencies import ContainerDep
from src.core.security import sanitize_input

logger = structlog.get_logger()
router = APIRouter()


class PredictionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    overrideConfig: dict[str, Any] | None = None  # noqa: N815 — Flowise convention


class PredictionResponse(BaseModel):
    text: str


@router.post(
    '/prediction/{chatflow_id}',
    response_model=PredictionResponse,
)
async def predict(
    chatflow_id: str,
    body: PredictionRequest,
    container: ContainerDep,
) -> PredictionResponse:
    """Flowise-compatible sync prediction — runs the agent and returns the answer."""
    sanitized = sanitize_input(body.question, container.settings)

    orchestrator = container.build_orchestrator()

    try:
        result = await orchestrator.run(
            user_id='widget-user',
            session_id=f'flowise-{chatflow_id}',
            message=sanitized,
        )
        logger.info(
            'prediction.done',
            chatflow_id=chatflow_id,
            tokens=result.total_tokens,
        )
        return PredictionResponse(text=result.answer)

    except Exception as exc:
        logger.error('prediction.error', error=str(exc))
        return PredictionResponse(text="Sorry, I wasn't able to help with that. Please try again.")
