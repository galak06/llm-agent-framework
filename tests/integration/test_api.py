"""Integration tests for API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.domain.schemas import RunStatus, RunStatusResponse
from tests.integration.conftest import WIDGET_KEY


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        resp = client.get('/api/v1/health')
        assert resp.status_code == 200
        data = resp.json()
        assert data['version'] == '1.0.0'
        assert 'status' in data
        assert 'checks' in data


class TestAskEndpoint:
    @patch('src.jobs.tasks.run_agent_task')
    def test_ask_returns_202_with_run_id(
        self, mock_task: MagicMock, client: TestClient, mock_container: MagicMock
    ) -> None:
        mock_container.result_store.set_status = AsyncMock()
        resp = client.post(
            '/api/v1/ask',
            json={'user_id': 'u1', 'session_id': 's1', 'message': 'Is rice safe?'},
            headers={'X-API-Key': WIDGET_KEY},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert 'run_id' in data
        assert 'status_url' in data
        assert data['status_url'].startswith('/api/v1/runs/')

    def test_ask_rejects_without_api_key(self, client: TestClient) -> None:
        resp = client.post(
            '/api/v1/ask',
            json={'user_id': 'u1', 'session_id': 's1', 'message': 'hello'},
        )
        assert resp.status_code == 401

    def test_ask_rejects_empty_message(self, client: TestClient) -> None:
        resp = client.post(
            '/api/v1/ask',
            json={'user_id': 'u1', 'session_id': 's1', 'message': ''},
            headers={'X-API-Key': WIDGET_KEY},
        )
        assert resp.status_code == 422

    def test_ask_rejects_missing_fields(self, client: TestClient) -> None:
        resp = client.post(
            '/api/v1/ask',
            json={'message': 'hello'},
            headers={'X-API-Key': WIDGET_KEY},
        )
        assert resp.status_code == 422


class TestRunsEndpoint:
    def test_get_run_returns_result(self, client: TestClient, mock_container: MagicMock) -> None:
        from datetime import UTC, datetime

        mock_container.result_store.get = AsyncMock(
            return_value=RunStatusResponse(
                run_id='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
                status=RunStatus.DONE,
                answer='Yes, rice is safe.',
                created_at=datetime.now(UTC),
            )
        )
        resp = client.get(
            '/api/v1/runs/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
            headers={'X-API-Key': WIDGET_KEY},
        )
        assert resp.status_code == 200
        assert resp.json()['answer'] == 'Yes, rice is safe.'

    def test_get_run_returns_404_for_missing(
        self, client: TestClient, mock_container: MagicMock
    ) -> None:
        mock_container.result_store.get = AsyncMock(return_value=None)
        resp = client.get(
            '/api/v1/runs/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
            headers={'X-API-Key': WIDGET_KEY},
        )
        assert resp.status_code == 404

    def test_get_run_rejects_invalid_uuid(self, client: TestClient) -> None:
        resp = client.get(
            '/api/v1/runs/not-a-uuid',
            headers={'X-API-Key': WIDGET_KEY},
        )
        assert resp.status_code == 422

    def test_get_run_rejects_without_api_key(self, client: TestClient) -> None:
        resp = client.get('/api/v1/runs/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')
        assert resp.status_code == 401
