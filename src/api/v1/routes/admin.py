from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field

from src.api.v1.middleware.api_key import require_admin_key

router = APIRouter(
    prefix='/admin',
    dependencies=[Depends(require_admin_key)],
)


class PromptUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=50000)


class PromptResponse(BaseModel):
    key: str
    content: str
    agent_name: str


PromptKey = Annotated[str, Path(min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_.-]+$')]


@router.get('/prompts', response_model=list[PromptResponse])
async def list_prompts() -> list[PromptResponse]:
    """List all prompts."""
    raise NotImplementedError


@router.put('/prompts/{key}', response_model=PromptResponse)
async def update_prompt(key: PromptKey, body: PromptUpdate) -> PromptResponse:
    """Update a prompt by key."""
    raise NotImplementedError
