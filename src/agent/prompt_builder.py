from __future__ import annotations

import structlog

from src.core.config import Settings
from src.memory.interfaces import MemoryReader

logger = structlog.get_logger()


class PromptBuilder:
    """Builds the prompt for the agent including system prompt, history, and memory."""

    def __init__(
        self,
        settings: Settings,
        memory: MemoryReader,
    ) -> None:
        self._settings = settings
        self._memory = memory
        self._system_prompt: str | None = None

    def set_system_prompt(self, prompt: str) -> None:
        self._system_prompt = prompt

    async def build(
        self,
        session_id: str,
        user_message: str,
    ) -> tuple[str | None, list[dict]]:
        """Build system prompt and messages list for LLM call."""
        history = await self._memory.get_history(session_id)
        relevant = await self._memory.search(user_message, top_k=self._settings.memory_top_k)

        messages: list[dict] = []

        for msg in history:
            messages.append({'role': msg.role.value, 'content': msg.content})

        messages.append({'role': 'user', 'content': user_message})

        logger.info(
            'prompt.build',
            session_id=session_id,
            history_count=len(history),
            memory_count=len(relevant),
        )
        return self._system_prompt, messages
