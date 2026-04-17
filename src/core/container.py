"""Service container — single place to build and access all shared dependencies."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.guardrails import GuardrailEngine
from src.agent.llm_client import create_llm_client
from src.agent.orchestrator import AgentOrchestrator
from src.agent.prompt_builder import PromptBuilder
from src.api.v1.answer_cache import AnswerCache
from src.api.v1.chat_rate_limit import ChatRateLimiter
from src.core.config import Settings
from src.db.engine import create_engine
from src.jobs.result_store import RunResultStore
from src.memory.session import RedisSessionMemory
from src.tools.registry import ToolRegistry


def _load_system_prompt(agent_name: str, prompt_key: str) -> str | None:
    """Load system prompt from agent seeds file."""
    seeds_path = Path('agents') / agent_name / 'seeds' / 'prompts.json'
    if not seeds_path.exists():
        return None
    prompts = json.loads(seeds_path.read_text())
    for prompt in prompts:
        if prompt.get('key') == prompt_key:
            return str(prompt['content'])
    return None


class ServiceContainer:
    """Lazily-built dependency graph. Created once at app startup."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # DB
        self.engine, self.session_factory = create_engine(settings)

        # Memory
        self.session_memory = RedisSessionMemory(settings)

        # Agent components
        self.llm_client = create_llm_client(settings)
        self.tool_registry = ToolRegistry()
        self.guardrails = GuardrailEngine(settings)
        self.prompt_builder = PromptBuilder(settings, self.session_memory)
        self.result_store = RunResultStore(settings)
        self.chat_rate_limiter = ChatRateLimiter(settings)
        self.answer_cache = AnswerCache(settings)

        # Load system prompt from seeds
        system_prompt = _load_system_prompt(
            settings.agent_name, settings.persona_system_prompt_key
        )
        if system_prompt:
            self.prompt_builder.set_system_prompt(system_prompt)

    def build_orchestrator(self) -> AgentOrchestrator:
        """Build a new orchestrator instance (stateless, safe to call per-request)."""
        return AgentOrchestrator(
            settings=self.settings,
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
            tool_registry=self.tool_registry,
            guardrails=self.guardrails,
            memory_writer=self.session_memory,
        )

    async def get_db_session(self) -> AsyncSession:
        return self.session_factory()
