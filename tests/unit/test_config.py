from __future__ import annotations

import pytest

from src.core.config import Settings


class TestSettings:
    def test_required_fields_present(self, settings: Settings) -> None:
        assert settings.widget_api_key == 'test-widget-key'
        assert settings.anthropic_api_key == 'sk-ant-test'
        assert settings.database_url.startswith('postgresql')

    def test_default_values(self, settings: Settings) -> None:
        assert settings.app_name == 'LLM Agent Framework'
        assert settings.app_env == 'development'
        assert settings.debug is False
        assert settings.llm_model == 'claude-sonnet-4-20250514'
        assert settings.agent_max_iterations == 5
        assert settings.rate_limit_requests == 10

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValueError):
            Settings(
                _env_file=None,
                anthropic_api_key='key',
                database_url='db',
                # missing widget_api_key and admin_api_key
            )

    def test_injection_patterns_parsed(self, settings: Settings) -> None:
        assert len(settings.injection_patterns) == 3
        assert 'jailbreak' in settings.injection_patterns

    def test_production_requires_widget_allowed_origins(self) -> None:
        with pytest.raises(ValueError, match='WIDGET_ALLOWED_ORIGINS'):
            Settings(
                _env_file=None,
                widget_api_key='test-widget-key',
                admin_api_key='test-admin-key',
                anthropic_api_key='sk-ant-test',
                database_url='postgresql+asyncpg://x',
                app_env='production',
                widget_allowed_origins=[],
            )

    def test_production_with_widget_allowed_origins_ok(self) -> None:
        s = Settings(
            _env_file=None,
            widget_api_key='test-widget-key',
            admin_api_key='test-admin-key',
            anthropic_api_key='sk-ant-test',
            database_url='postgresql+asyncpg://x',
            app_env='production',
            widget_allowed_origins=['https://example.com'],
        )
        assert s.app_env == 'production'

    def test_development_with_empty_allowlist_ok(self) -> None:
        s = Settings(
            _env_file=None,
            widget_api_key='test-widget-key',
            admin_api_key='test-admin-key',
            anthropic_api_key='sk-ant-test',
            database_url='postgresql+asyncpg://x',
            app_env='development',
            widget_allowed_origins=[],
        )
        assert s.widget_allowed_origins == []
