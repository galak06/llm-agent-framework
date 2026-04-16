from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import GuardrailViolationError, TokenBudgetExceededError
from src.domain.schemas import AgentRunResult, RunStatus
from src.jobs.tasks import _execute_agent


class TestExecuteAgent:
    """Tests for the async _execute_agent inner function."""

    @pytest.fixture
    def request_dict(self) -> dict[str, str]:
        return {
            'user_id': 'test-user',
            'session_id': 'test-session',
            'message': 'Can my dog eat rice?',
        }

    @pytest.fixture
    def mock_store(self) -> AsyncMock:
        store = AsyncMock()
        store.set_status = AsyncMock()
        store.set_result = AsyncMock()
        return store

    @pytest.fixture
    def mock_orchestrator(self) -> AsyncMock:
        orch = AsyncMock()
        orch.run = AsyncMock(
            return_value=AgentRunResult(
                answer='Yes, rice is safe for dogs.',
                tools_used=['ingredient_checker@1.0.0'],
                total_tokens=150,
                iterations=1,
            )
        )
        return orch

    @pytest.mark.asyncio
    async def test_successful_run_sets_done(
        self, request_dict: dict[str, str], mock_store: AsyncMock, mock_orchestrator: AsyncMock
    ) -> None:
        with (
            patch('src.core.config.get_settings', return_value=MagicMock()),
            patch('src.jobs.result_store.RunResultStore', return_value=mock_store),
            patch('src.memory.session.RedisSessionMemory'),
            patch('src.agent.llm_client.LLMClient'),
            patch('src.agent.prompt_builder.PromptBuilder'),
            patch('src.tools.registry.ToolRegistry'),
            patch('src.agent.guardrails.GuardrailEngine'),
            patch(
                'src.agent.orchestrator.AgentOrchestrator',
                return_value=mock_orchestrator,
            ),
        ):
            await _execute_agent(request_dict, 'run-123')

        mock_store.set_status.assert_called_once_with('run-123', RunStatus.RUNNING)
        mock_store.set_result.assert_called_once()
        result_arg = mock_store.set_result.call_args[0][1]
        assert result_arg.status == RunStatus.DONE
        assert result_arg.answer == 'Yes, rice is safe for dogs.'
        assert result_arg.total_tokens == 150

    @pytest.mark.asyncio
    async def test_guardrail_violation_sets_failed(
        self, request_dict: dict[str, str], mock_store: AsyncMock
    ) -> None:
        mock_orch = AsyncMock()
        mock_orch.run = AsyncMock(side_effect=GuardrailViolationError('Injection detected'))

        with (
            patch('src.core.config.get_settings', return_value=MagicMock()),
            patch('src.jobs.result_store.RunResultStore', return_value=mock_store),
            patch('src.memory.session.RedisSessionMemory'),
            patch('src.agent.llm_client.LLMClient'),
            patch('src.agent.prompt_builder.PromptBuilder'),
            patch('src.tools.registry.ToolRegistry'),
            patch('src.agent.guardrails.GuardrailEngine'),
            patch('src.agent.orchestrator.AgentOrchestrator', return_value=mock_orch),
        ):
            await _execute_agent(request_dict, 'run-456')

        result_arg = mock_store.set_result.call_args[0][1]
        assert result_arg.status == RunStatus.FAILED
        assert 'Injection detected' in (result_arg.error or '')

    @pytest.mark.asyncio
    async def test_token_budget_exceeded_sets_failed(
        self, request_dict: dict[str, str], mock_store: AsyncMock
    ) -> None:
        mock_orch = AsyncMock()
        mock_orch.run = AsyncMock(side_effect=TokenBudgetExceededError('Max iterations'))

        with (
            patch('src.core.config.get_settings', return_value=MagicMock()),
            patch('src.jobs.result_store.RunResultStore', return_value=mock_store),
            patch('src.memory.session.RedisSessionMemory'),
            patch('src.agent.llm_client.LLMClient'),
            patch('src.agent.prompt_builder.PromptBuilder'),
            patch('src.tools.registry.ToolRegistry'),
            patch('src.agent.guardrails.GuardrailEngine'),
            patch('src.agent.orchestrator.AgentOrchestrator', return_value=mock_orch),
        ):
            await _execute_agent(request_dict, 'run-789')

        result_arg = mock_store.set_result.call_args[0][1]
        assert result_arg.status == RunStatus.FAILED
        assert 'Max iterations' in (result_arg.error or '')

    @pytest.mark.asyncio
    async def test_unexpected_error_sets_failed_and_reraises(
        self, request_dict: dict[str, str], mock_store: AsyncMock
    ) -> None:
        mock_orch = AsyncMock()
        mock_orch.run = AsyncMock(side_effect=RuntimeError('boom'))

        with (
            patch('src.core.config.get_settings', return_value=MagicMock()),
            patch('src.jobs.result_store.RunResultStore', return_value=mock_store),
            patch('src.memory.session.RedisSessionMemory'),
            patch('src.agent.llm_client.LLMClient'),
            patch('src.agent.prompt_builder.PromptBuilder'),
            patch('src.tools.registry.ToolRegistry'),
            patch('src.agent.guardrails.GuardrailEngine'),
            patch('src.agent.orchestrator.AgentOrchestrator', return_value=mock_orch),
            pytest.raises(RuntimeError, match='boom'),
        ):
            await _execute_agent(request_dict, 'run-err')

        result_arg = mock_store.set_result.call_args[0][1]
        assert result_arg.status == RunStatus.FAILED
        assert 'RuntimeError' in (result_arg.error or '')
