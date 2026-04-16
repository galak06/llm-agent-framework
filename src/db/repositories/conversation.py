from __future__ import annotations

import uuid

from sqlalchemy import select

from src.db.models import Conversation, ConversationMessage
from src.db.repositories.base import BaseRepository


class ConversationRepository(BaseRepository):
    """Repository for conversations and messages."""

    async def get_or_create(self, user_id: str, session_id: str) -> Conversation:
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.session_id == session_id,
        )
        result = await self._session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation is None:
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=user_id,
                session_id=session_id,
            )
            self._session.add(conversation)
            await self._session.flush()
        return conversation

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
    ) -> ConversationMessage:
        message = ConversationMessage(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ConversationMessage]:
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
