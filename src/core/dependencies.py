from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.container import ServiceContainer

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_container(request: Request) -> ServiceContainer:
    """Retrieve the ServiceContainer from app state."""
    return request.app.state.container  # type: ignore[no-any-return]


ContainerDep = Annotated[ServiceContainer, Depends(get_container)]


async def get_db_session(
    container: ContainerDep,
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, auto-commit on success, rollback on error."""
    async with container.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
