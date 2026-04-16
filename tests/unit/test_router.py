from __future__ import annotations

import pytest

from src.agent.router import ConfigRouter
from src.core.exceptions import RouterError
from src.domain.schemas import AskRequest


class FakeOrchestrator:
    def __init__(self, name: str) -> None:
        self.name = name


class TestConfigRouter:
    def _make_router(self) -> ConfigRouter:
        orchestrators = {
            'general': FakeOrchestrator('general'),  # type: ignore[arg-type]
            'nutrition': FakeOrchestrator('nutrition'),  # type: ignore[arg-type]
        }
        rules = [
            {'agent': 'nutrition', 'match_any_keywords': ['protein', 'calories']},
            {'agent': 'general', 'match_any_keywords': ['safe', 'eat', 'toxic']},
        ]
        return ConfigRouter(orchestrators=orchestrators, rules=rules, default='general')

    def test_routes_to_matching_agent(self) -> None:
        router = self._make_router()
        request = AskRequest(user_id='u1', session_id='s1', message='How much protein in chicken?')
        result = router.route(request)
        assert result.name == 'nutrition'  # type: ignore[attr-defined]

    def test_routes_to_second_rule(self) -> None:
        router = self._make_router()
        request = AskRequest(user_id='u1', session_id='s1', message='Can dogs eat chocolate?')
        result = router.route(request)
        assert result.name == 'general'  # type: ignore[attr-defined]

    def test_falls_back_to_default(self) -> None:
        router = self._make_router()
        request = AskRequest(user_id='u1', session_id='s1', message='What time is it?')
        result = router.route(request)
        assert result.name == 'general'  # type: ignore[attr-defined]

    def test_case_insensitive_match(self) -> None:
        router = self._make_router()
        request = AskRequest(user_id='u1', session_id='s1', message='PROTEIN content?')
        result = router.route(request)
        assert result.name == 'nutrition'  # type: ignore[attr-defined]

    def test_missing_agent_raises(self) -> None:
        orchestrators = {'general': FakeOrchestrator('general')}  # type: ignore[dict-item]
        rules = [{'agent': 'missing', 'match_any_keywords': ['test']}]
        router = ConfigRouter(orchestrators=orchestrators, rules=rules, default='general')
        request = AskRequest(user_id='u1', session_id='s1', message='test query')
        with pytest.raises(RouterError):
            router.route(request)
