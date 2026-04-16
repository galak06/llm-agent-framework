from __future__ import annotations

from datetime import datetime

from src.domain.schemas import (
    AgentRunResult,
    AskRequest,
    AskResponse,
    GuardrailResult,
    HealthResponse,
    Message,
    Role,
    RunStatus,
    RunStatusResponse,
    ServiceStatus,
    ToolResult,
)


class TestEnums:
    def test_role_values(self) -> None:
        assert Role.USER == 'user'
        assert Role.ASSISTANT == 'assistant'
        assert Role.TOOL == 'tool'

    def test_run_status_values(self) -> None:
        assert RunStatus.PENDING == 'pending'
        assert RunStatus.DONE == 'done'

    def test_service_status_values(self) -> None:
        assert ServiceStatus.OK == 'ok'
        assert ServiceStatus.DEGRADED == 'degraded'


class TestRequestModels:
    def test_ask_request(self) -> None:
        req = AskRequest(user_id='u1', session_id='s1', message='hello')
        assert req.user_id == 'u1'
        assert req.message == 'hello'

    def test_ask_response(self) -> None:
        resp = AskResponse(run_id='r1', status_url='/runs/r1')
        assert resp.run_id == 'r1'

    def test_run_status_response_defaults(self) -> None:
        resp = RunStatusResponse(
            run_id='r1',
            status=RunStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        assert resp.answer is None
        assert resp.tools_used == []
        assert resp.error is None


class TestAgentModels:
    def test_message_has_uuid(self) -> None:
        msg = Message(role=Role.USER, content='hi')
        assert msg.id is not None
        assert len(msg.id) > 0

    def test_tool_result(self) -> None:
        result = ToolResult(tool_name='check', output='safe')
        assert result.error is None

    def test_agent_run_result(self) -> None:
        result = AgentRunResult(answer='yes', iterations=2)
        assert result.total_tokens == 0
        assert result.tools_used == []

    def test_guardrail_result(self) -> None:
        result = GuardrailResult(passed=True)
        assert result.reason is None

    def test_health_response(self) -> None:
        resp = HealthResponse(
            status=ServiceStatus.OK,
            version='1.0.0',
            uptime_seconds=42.0,
            checks={'redis': ServiceStatus.OK},
        )
        assert resp.checks['redis'] == ServiceStatus.OK
