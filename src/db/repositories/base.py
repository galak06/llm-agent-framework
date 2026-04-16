from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Base repository with shared session access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
