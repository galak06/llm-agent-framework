from __future__ import annotations

import anthropic.types
import structlog

from src.agent.guardrails import GuardrailEngine
from src.agent.llm_client import LLMClient
from src.agent.prompt_builder import PromptBuilder
from src.core.config import Settings
from src.core.exceptions import GuardrailViolationError, TokenBudgetExceededError
from src.domain.schemas import AgentRunResult, Message, Role
from src.memory.interfaces import MemoryWriter
from src.tools.registry import ToolRegistry

logger = structlog.get_logger()


class AgentOrchestrator:
    """Main agent loop: prompt → LLM → tool use → repeat until done."""

    def __init__(
        self,
        settings: Settings,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder,
        tool_registry: ToolRegistry,
        guardrails: GuardrailEngine,
        memory_writer: MemoryWriter,
    ) -> None:
        self._settings = settings
        self._llm = llm_client
        self._prompt_builder = prompt_builder
        self._tools = tool_registry
        self._guardrails = guardrails
        self._memory = memory_writer
        self._max_iterations = settings.agent_max_iterations

    async def run(
        self,
        user_id: str,
        session_id: str,
        message: str,
    ) -> AgentRunResult:
        """Execute the full agent loop."""
        input_check = self._guardrails.check_input(message)
        if not input_check.passed:
            raise GuardrailViolationError(input_check.reason)

        await self._memory.add(
            session_id,
            Message(role=Role.USER, content=message),
        )

        system_prompt, messages = await self._prompt_builder.build(session_id, message)
        tool_schemas = self._tools.get_schemas()

        tools_used: list[str] = []
        total_tokens = 0

        for iteration in range(self._max_iterations):
            logger.info('agent.iteration', iteration=iteration, user_id=user_id)

            response = await self._llm.chat(
                messages=messages,
                system=system_prompt,
                tools=tool_schemas if tool_schemas else None,
            )

            total_tokens += response.usage.input_tokens + response.usage.output_tokens

            if response.stop_reason == 'end_turn':
                answer = self._extract_text(response)
                output_check = self._guardrails.check_output(answer)
                if not output_check.passed:
                    answer = self._settings.fallback_message_key

                await self._memory.add(
                    session_id,
                    Message(role=Role.ASSISTANT, content=answer),
                )

                return AgentRunResult(
                    answer=answer,
                    tools_used=tools_used,
                    total_tokens=total_tokens,
                    iterations=iteration + 1,
                )

            if response.stop_reason == 'tool_use':
                for block in response.content:
                    if block.type == 'tool_use':
                        result = await self._tools.execute_tool(
                            block.name,
                            **block.input,
                        )
                        tools_used.append(self._tools.get(block.name).versioned_name)
                        messages.append(
                            {
                                'role': 'assistant',
                                'content': response.content,
                            }
                        )
                        messages.append(
                            {
                                'role': 'user',
                                'content': [
                                    {
                                        'type': 'tool_result',
                                        'tool_use_id': block.id,
                                        'content': result.output
                                        if not result.error
                                        else result.error,
                                    }
                                ],
                            }
                        )

        raise TokenBudgetExceededError(f'Agent exceeded max iterations ({self._max_iterations})')

    @staticmethod
    def _extract_text(response: anthropic.types.Message) -> str:
        """Extract text content from LLM response."""
        parts = []
        for block in response.content:
            if hasattr(block, 'text'):
                parts.append(block.text)
        return '\n'.join(parts)
