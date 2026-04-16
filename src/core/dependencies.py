from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.db.engine import create_engine

SettingsDep = Annotated[Settings, Depends(get_settings)]

_engine_cache: dict[str, AsyncSession] = {}


async def get_db_session(
    settings: SettingsDep,
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, auto-commit on success, rollback on error."""
    _, session_factory = create_engine(settings)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
