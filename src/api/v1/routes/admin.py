from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from src.api.v1.middleware.api_key import require_admin_key
from src.core.dependencies import DbSessionDep
from src.db.repositories.prompt import PromptRepository

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
async def list_prompts(session: DbSessionDep) -> list[PromptResponse]:
    """List all prompts."""
    repo = PromptRepository(session)
    prompts = await repo.list_all()
    return [PromptResponse(key=p.key, content=p.content, agent_name=p.agent_name) for p in prompts]


@router.put('/prompts/{key}', response_model=PromptResponse)
async def update_prompt(
    key: PromptKey, body: PromptUpdate, session: DbSessionDep
) -> PromptResponse:
    """Create or update a prompt by key."""
    repo = PromptRepository(session)
    prompt = await repo.upsert(key=key, content=body.content)
    return PromptResponse(
        key=prompt.key,
        content=prompt.content,
        agent_name=prompt.agent_name,
    )


@router.get('/prompts/{key}', response_model=PromptResponse)
async def get_prompt(key: PromptKey, session: DbSessionDep) -> PromptResponse:
    """Get a single prompt by key."""
    repo = PromptRepository(session)
    prompt = await repo.get_by_key(key)
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Prompt not found: {key}',
        )
    return PromptResponse(
        key=prompt.key,
        content=prompt.content,
        agent_name=prompt.agent_name,
    )
