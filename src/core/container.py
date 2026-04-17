"""Service container — single place to build and access all shared dependencies."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.guardrails import GuardrailEngine
from src.agent.llm_client import create_llm_client
from src.agent.orchestrator import AgentOrchestrator
from src.agent.prompt_builder import PromptBuilder
from src.core.config import Settings
from src.db.engine import create_engine
from src.jobs.result_store import RunResultStore
from src.memory.session import RedisSessionMemory
from src.tools.registry import ToolRegistry


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
