from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import structlog

from src.core.exceptions import RouterError
from src.domain.schemas import AskRequest

if TYPE_CHECKING:
    from src.agent.orchestrator import AgentOrchestrator

logger = structlog.get_logger()


class AgentRouter(Protocol):
    """Routes an incoming request to the appropriate AgentOrchestrator."""

    def route(self, request: AskRequest) -> AgentOrchestrator: ...


class ConfigRouter:
    """Routes based on keyword rules from agents/{name}/router_config.json."""

    def __init__(
        self,
        orchestrators: dict[str, AgentOrchestrator],
        rules: list[dict[str, object]],
        default: str,
    ) -> None:
        self._orchestrators = orchestrators
        self._rules = rules
        self._default = default

    def route(self, request: AskRequest) -> AgentOrchestrator:
        message_lower = request.message.lower()

        for rule in self._rules:
            raw_keywords = rule.get('match_any_keywords', [])
            keywords: list[str] = list(raw_keywords) if isinstance(raw_keywords, list) else []
            if any(kw in message_lower for kw in keywords):
                agent_name = rule['agent']
                logger.info(
                    'router.match',
                    agent=agent_name,
                    keyword_matched=True,
                )
                if agent_name not in self._orchestrators:
                    raise RouterError(f'Agent not found: {agent_name}')
                return self._orchestrators[agent_name]

        logger.info('router.default', agent=self._default)
        if self._default not in self._orchestrators:
            raise RouterError(f'Default agent not found: {self._default}')
        return self._orchestrators[self._default]
