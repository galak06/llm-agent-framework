from __future__ import annotations


class TestRateLimitConfig:
    """Rate limit unit tests — integration tests cover Redis-backed behavior."""

    def test_rate_limit_settings_defaults(self) -> None:
        from src.core.config import Settings

        settings = Settings(
            _env_file=None,
            widget_api_key='k',
            admin_api_key='k',
            anthropic_api_key='k',
            database_url='postgresql+asyncpg://x',
        )
        assert settings.rate_limit_requests == 10
        assert settings.rate_limit_window_seconds == 60

    def test_rate_limit_settings_custom(self) -> None:
        from src.core.config import Settings

        settings = Settings(
            _env_file=None,
            widget_api_key='k',
            admin_api_key='k',
            anthropic_api_key='k',
            database_url='postgresql+asyncpg://x',
            rate_limit_requests=100,
            rate_limit_window_seconds=300,
        )
        assert settings.rate_limit_requests == 100
        assert settings.rate_limit_window_seconds == 300
