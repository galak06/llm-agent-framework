from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any, Protocol

import structlog

from src.core.config import Settings
from src.domain.schemas import ImageInput

logger = structlog.get_logger()


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMTextBlock:
    type: str = 'text'
    text: str = ''


@dataclass
class LLMResponse:
    """Provider-agnostic LLM response."""

    content: list[LLMTextBlock] = field(default_factory=list)
    stop_reason: str = 'end_turn'
    usage: LLMUsage = field(default_factory=LLMUsage)


class LLMClientProtocol(Protocol):
    async def chat(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, object]] | None = None,
        images: list[ImageInput] | None = None,
    ) -> LLMResponse: ...


class AnthropicLLMClient:
    """Wraps the Anthropic SDK for agent LLM calls."""

    def __init__(self, settings: Settings) -> None:
        import anthropic

        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens

    async def chat(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, object]] | None = None,
        images: list[ImageInput] | None = None,
    ) -> LLMResponse:
        if images:
            messages = _attach_images_anthropic(messages, images)

        kwargs: dict[str, Any] = {
            'model': self._model,
            'max_tokens': self._max_tokens,
            'messages': messages,
        }
        if system is not None:
            kwargs['system'] = system
        if tools:
            kwargs['tools'] = tools

        logger.info('llm.call', provider='anthropic', model=self._model, images=len(images or []))
        response = await self._client.messages.create(**kwargs)
        logger.info(
            'llm.response',
            provider='anthropic',
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        blocks = [LLMTextBlock(text=b.text) for b in response.content if hasattr(b, 'text')]
        return LLMResponse(
            content=blocks,
            stop_reason=response.stop_reason or 'end_turn',
            usage=LLMUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
        )


class GeminiLLMClient:
    """Wraps the Google GenAI SDK for agent LLM calls."""

    def __init__(self, settings: Settings) -> None:
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens

    async def chat(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, object]] | None = None,
        images: list[ImageInput] | None = None,
    ) -> LLMResponse:
        from google.genai import types

        contents: list[types.Content] = []
        for msg in messages:
            role = 'model' if msg.get('role') == 'assistant' else 'user'
            text = msg.get('content', '')
            if isinstance(text, str):
                contents.append(types.Content(role=role, parts=[types.Part(text=text)]))

        if images and contents and contents[-1].role == 'user':
            last = contents[-1]
            image_parts = [
                types.Part(inline_data=types.Blob(mime_type=img.mime_type, data=img.data))
                for img in images
            ]
            last.parts = image_parts + list(last.parts or [])

        config = types.GenerateContentConfig(
            max_output_tokens=self._max_tokens,
        )
        if system:
            config.system_instruction = system

        logger.info('llm.call', provider='gemini', model=self._model, images=len(images or []))
        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,  # type: ignore[arg-type]
            config=config,
        )

        text = response.text or ''
        input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
        output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0

        logger.info(
            'llm.response',
            provider='gemini',
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return LLMResponse(
            content=[LLMTextBlock(text=text)],
            stop_reason='end_turn',
            usage=LLMUsage(input_tokens=input_tokens, output_tokens=output_tokens),
        )


def _attach_images_anthropic(
    messages: list[dict[str, Any]], images: list[ImageInput]
) -> list[dict[str, Any]]:
    """Return a copy of messages with images prepended to the last user message."""
    if not messages or messages[-1].get('role') != 'user':
        return messages

    image_blocks: list[dict[str, Any]] = [
        {
            'type': 'image',
            'source': {
                'type': 'base64',
                'media_type': img.mime_type,
                'data': base64.b64encode(img.data).decode('ascii'),
            },
        }
        for img in images
    ]

    last = messages[-1]
    existing = last.get('content', '')
    text_blocks: list[dict[str, Any]]
    if isinstance(existing, str):
        text_blocks = [{'type': 'text', 'text': existing}] if existing else []
    else:
        text_blocks = list(existing)

    new_messages = list(messages[:-1])
    new_messages.append({'role': 'user', 'content': image_blocks + text_blocks})
    return new_messages


def create_llm_client(settings: Settings) -> LLMClientProtocol:
    """Factory: pick LLM provider based on config."""
    if settings.llm_provider == 'gemini':
        return GeminiLLMClient(settings)
    return AnthropicLLMClient(settings)
