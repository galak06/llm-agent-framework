from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.middleware.request_id import RequestIDMiddleware
from src.api.v1.routes import admin, chat, health
from src.core.config import Settings, get_settings
from src.core.dependencies import get_container, get_db_session

WIDGET_KEY = 'test-widget-key'
ADMIN_KEY = 'test-admin-key'


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        widget_api_key=WIDGET_KEY,
        admin_api_key=ADMIN_KEY,
        anthropic_api_key='sk-ant-test',
        database_url='postgresql+asyncpg://test:test@localhost:5432/test',
        redis_url=os.environ.get('REDIS_URL', 'redis://localhost:6379'),
        injection_patterns=['ignore previous instructions', 'jailbreak'],
        forbidden_output_patterns=['diagnose', 'prescribe'],
    )


@pytest.fixture
def mock_container(settings: Settings) -> MagicMock:
    """A mock container for API tests that don't need real services."""
    container = MagicMock()
    container.settings = settings
    container.result_store = AsyncMock()
    container.engine = MagicMock()
    container.session_factory = MagicMock()
    container.build_orchestrator = MagicMock()
    return container


def _create_test_app(settings: Settings) -> FastAPI:
    """Build a minimal FastAPI app without Redis-dependent middleware."""
    app = FastAPI(title='test')
    app.add_middleware(RequestIDMiddleware)
    prefix = f'/api/{settings.api_version}'
    app.include_router(health.router, prefix=prefix)
    app.include_router(chat.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)
    return app


@pytest.fixture
def client(settings: Settings, mock_container: MagicMock) -> TestClient:
    """TestClient with mocked container (no real Redis/DB needed)."""
    app = _create_test_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_container] = lambda: mock_container

    async def mock_db_session():  # type: ignore[no-untyped-def]
        yield AsyncMock()

    app.dependency_overrides[get_db_session] = mock_db_session
    return TestClient(app)
