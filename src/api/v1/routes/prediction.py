"""Flowise-compatible prediction endpoint.

Accepts POST /api/v1/prediction/{chatflowid} with {"question": "...", "uploads": [...]}
and returns {"text": "..."} synchronously.
"""

from __future__ import annotations

import base64
import binascii
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.core.config import Settings
from src.core.dependencies import ContainerDep
from src.core.security import sanitize_input
from src.domain.schemas import ImageInput

logger = structlog.get_logger()
router = APIRouter()


class FlowiseUpload(BaseModel):
    """A single upload as sent by the flowise-embed widget."""

    data: str = Field(min_length=1)
    type: str | None = None
    name: str | None = None
    mime: str | None = None


class PredictionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    uploads: list[FlowiseUpload] | None = None
    overrideConfig: dict[str, Any] | None = None  # noqa: N815 — Flowise convention


class PredictionResponse(BaseModel):
    text: str


def _parse_uploads(uploads: list[FlowiseUpload] | None, settings: Settings) -> list[ImageInput]:
    """Validate and decode flowise uploads into ImageInput objects.

    Raises HTTPException 400 on any validation failure.
    """
    if not uploads:
        return []

    if len(uploads) > settings.image_max_per_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Too many uploads (max {settings.image_max_per_request})',
        )

    images: list[ImageInput] = []
    for upload in uploads:
        mime, payload = _split_data_url(upload.data, upload.mime)

        if mime not in settings.image_allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unsupported image type: {mime}',
            )

        try:
            data = base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid base64 image data',
            ) from exc

        if len(data) > settings.image_max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Image exceeds size limit ({settings.image_max_bytes} bytes)',
            )

        images.append(ImageInput(mime_type=mime, data=data))

    return images


def _split_data_url(data: str, fallback_mime: str | None) -> tuple[str, str]:
    """Split a data URL into (mime, base64_payload).

    Accepts either a full data URL (``data:image/png;base64,...``) or a bare base64
    string — in the latter case ``fallback_mime`` is used.
    """
    if data.startswith('data:'):
        try:
            header, payload = data.split(',', 1)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Malformed data URL',
            ) from exc
        mime = header.removeprefix('data:').split(';', 1)[0] or (fallback_mime or '')
        return mime, payload
    return (fallback_mime or ''), data


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
    images = _parse_uploads(body.uploads, container.settings)

    orchestrator = container.build_orchestrator()

    try:
        result = await orchestrator.run(
            user_id='widget-user',
            session_id=f'flowise-{chatflow_id}',
            message=sanitized,
            images=images or None,
        )
        logger.info(
            'prediction.done',
            chatflow_id=chatflow_id,
            tokens=result.total_tokens,
            images=len(images),
        )
        return PredictionResponse(text=result.answer)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error('prediction.error', error=str(exc))
        return PredictionResponse(text="Sorry, I wasn't able to help with that. Please try again.")
