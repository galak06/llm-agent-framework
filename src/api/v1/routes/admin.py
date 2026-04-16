from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.v1.middleware.api_key import require_admin_key

router = APIRouter(
    prefix='/admin',
    dependencies=[Depends(require_admin_key)],
)


class PromptUpdate(BaseModel):
    content: str


class PromptResponse(BaseModel):
    key: str
    content: str
    agent_name: str


@router.get('/prompts', response_model=list[PromptResponse])
async def list_prompts() -> list[PromptResponse]:
    """List all prompts."""
    raise NotImplementedError


@router.put('/prompts/{key}', response_model=PromptResponse)
async def update_prompt(key: str, body: PromptUpdate) -> PromptResponse:
    """Update a prompt by key."""
    raise NotImplementedError
