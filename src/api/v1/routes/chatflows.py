"""Flowise-compatible chatflow capability preflight.

flowise-embed fetches GET /api/v1/public-chatflows/:id on init to decide which
UI affordances to render (upload button, streaming, audio, etc.). If the
endpoint 404s, the client hides the upload button regardless of the
chatflowConfig.uploads passed from the embedder.

We synthesize a minimal response from Settings so the widget picks up our
upload caps without a real Flowise backend behind it.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from src.core.dependencies import ContainerDep

router = APIRouter()


def _chatbot_config(container: ContainerDep) -> dict[str, Any]:
    settings = container.settings
    max_size_mb = max(1, settings.image_max_bytes // (1024 * 1024))
    return {
        'uploads': {
            'isImageUploadAllowed': True,
            'imgUploadSizeAndTypes': [
                {
                    'fileTypes': list(settings.image_allowed_mime_types),
                    'maxUploadSize': max_size_mb,
                }
            ],
        },
    }


@router.get('/public-chatflows/{chatflow_id}')
async def get_public_chatflow(chatflow_id: str, container: ContainerDep) -> dict[str, Any]:
    """Return Flowise-shaped chatflow metadata so the widget enables uploads."""
    now = datetime.now(UTC).isoformat()
    return {
        'id': chatflow_id,
        'name': chatflow_id,
        'flowData': '{}',
        'deployed': True,
        'isPublic': True,
        'apikeyid': None,
        'chatbotConfig': json.dumps(_chatbot_config(container)),
        'createdDate': now,
        'updatedDate': now,
        'type': 'CHATFLOW',
    }


@router.get('/public-chatbotConfig/{chatflow_id}')
async def get_public_chatbot_config(chatflow_id: str, container: ContainerDep) -> dict[str, Any]:
    """Newer flowise-embed variants query this path directly for chatbotConfig."""
    return _chatbot_config(container)
