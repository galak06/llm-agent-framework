from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.routes.admin import router
from src.core.config import Settings, get_settings
from src.core.dependencies import get_db_session

ADMIN_KEY = 'test-admin-key'


def _make_test_settings() -> Settings:
    return Settings(
        _env_file=None,
        widget_api_key='test-widget-key',
        admin_api_key=ADMIN_KEY,
        anthropic_api_key='sk-ant-test',
        database_url='postgresql+asyncpg://test:test@localhost/test',
    )


class TestAdminRoutes:
    """Tests for admin prompt CRUD routes."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_session: AsyncMock) -> TestClient:
        app = FastAPI()
        app.include_router(router, prefix='/api/v1')

        async def override_session():  # type: ignore[no-untyped-def]
            yield mock_session

        app.dependency_overrides[get_db_session] = override_session
        app.dependency_overrides[get_settings] = _make_test_settings
        return TestClient(app, headers={'X-API-Key': ADMIN_KEY})

    @pytest.fixture
    def mock_prompt(self) -> MagicMock:
        p = MagicMock()
        p.key = 'system_base'
        p.content = 'You are a helpful assistant.'
        p.agent_name = 'default'
        return p

    def test_list_prompts_empty(self, client: TestClient, mock_session: AsyncMock) -> None:
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: []))
        )
        resp = client.get('/api/v1/admin/prompts')
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_prompts_returns_data(
        self, client: TestClient, mock_session: AsyncMock, mock_prompt: MagicMock
    ) -> None:
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_prompt]))
        )
        resp = client.get('/api/v1/admin/prompts')
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['key'] == 'system_base'

    def test_get_prompt_not_found(self, client: TestClient, mock_session: AsyncMock) -> None:
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
        resp = client.get('/api/v1/admin/prompts/nonexistent')
        assert resp.status_code == 404

    def test_get_prompt_found(
        self, client: TestClient, mock_session: AsyncMock, mock_prompt: MagicMock
    ) -> None:
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=lambda: mock_prompt)
        )
        resp = client.get('/api/v1/admin/prompts/system_base')
        assert resp.status_code == 200
        assert resp.json()['key'] == 'system_base'

    def test_update_prompt_validates_empty_content(self, client: TestClient) -> None:
        resp = client.put(
            '/api/v1/admin/prompts/test_key',
            json={'content': ''},
        )
        assert resp.status_code == 422

    def test_update_prompt_validates_key_format(self, client: TestClient) -> None:
        resp = client.put(
            '/api/v1/admin/prompts/invalid key!',
            json={'content': 'some content'},
        )
        assert resp.status_code == 422

    def test_requires_admin_api_key(self) -> None:
        app = FastAPI()
        app.include_router(router, prefix='/api/v1')
        app.dependency_overrides[get_settings] = _make_test_settings

        async def override_session():  # type: ignore[no-untyped-def]
            yield AsyncMock()

        app.dependency_overrides[get_db_session] = override_session
        no_key_client = TestClient(app)
        resp = no_key_client.get('/api/v1/admin/prompts')
        assert resp.status_code == 401
