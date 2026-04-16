from __future__ import annotations

import pytest

from src.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        widget_api_key='test-widget-key',
        admin_api_key='test-admin-key',
        anthropic_api_key='sk-ant-test',
        database_url='postgresql+asyncpg://test:test@localhost:5432/test',
        redis_url='redis://localhost:6379',
        injection_patterns=['ignore previous instructions', 'jailbreak'],
        forbidden_output_patterns=['diagnose', 'prescribe'],
    )
