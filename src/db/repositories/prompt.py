from __future__ import annotations

from sqlalchemy import select

from src.db.models import Prompt
from src.db.repositories.base import BaseRepository


class PromptRepository(BaseRepository):
    """Repository for managing prompts."""

    async def get_by_key(self, key: str, agent_name: str = 'default') -> Prompt | None:
        stmt = select(Prompt).where(
            Prompt.key == key,
            Prompt.agent_name == agent_name,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, key: str, content: str, agent_name: str = 'default') -> Prompt:
        existing = await self.get_by_key(key, agent_name)
        if existing is not None:
            existing.content = content
            await self._session.flush()
            return existing
        prompt = Prompt(key=key, content=content, agent_name=agent_name)
        self._session.add(prompt)
        await self._session.flush()
        return prompt

    async def list_all(self, agent_name: str | None = None) -> list[Prompt]:
        stmt = select(Prompt)
        if agent_name is not None:
            stmt = stmt.where(Prompt.agent_name == agent_name)
        stmt = stmt.order_by(Prompt.key)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
