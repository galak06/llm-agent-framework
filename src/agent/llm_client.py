from __future__ import annotations

import anthropic
import structlog

from src.core.config import Settings

logger = structlog.get_logger()


class LLMClient:
    """Wraps the Anthropic SDK for agent LLM calls."""

    def __init__(self, settings: Settings) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens

    async def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
    ) -> anthropic.types.Message:
        kwargs: dict = {
            'model': self._model,
            'max_tokens': self._max_tokens,
            'messages': messages,
        }
        if system is not None:
            kwargs['system'] = system
        if tools:
            kwargs['tools'] = tools

        logger.info('llm.call', model=self._model, message_count=len(messages))
        response = await self._client.messages.create(**kwargs)
        logger.info(
            'llm.response',
            model=self._model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return response
