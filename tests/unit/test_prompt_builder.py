from __future__ import annotations

from src.domain.schemas import Message, Role


class TestPromptBuilderModels:
    """Unit tests for prompt builder data structures."""

    def test_message_role_user(self) -> None:
        msg = Message(role=Role.USER, content='hello')
        assert msg.role == Role.USER

    def test_message_role_assistant(self) -> None:
        msg = Message(role=Role.ASSISTANT, content='hi there')
        assert msg.role == Role.ASSISTANT

    def test_message_serialization(self) -> None:
        msg = Message(role=Role.USER, content='test')
        data = msg.model_dump()
        assert data['role'] == 'user'
        assert data['content'] == 'test'
