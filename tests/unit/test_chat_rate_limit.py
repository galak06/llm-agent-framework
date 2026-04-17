from __future__ import annotations

from src.core.config import Settings


class TestChatRateLimitConfig:
    """ChatRateLimiter unit tests — integration tests cover Redis-backed behavior."""

    def test_defaults(self) -> None:
        settings = Settings(
            _env_file=None,
            widget_api_key='test-key-1234',
            admin_api_key='test-key-1234',
            anthropic_api_key='sk-ant-test',
            database_url='postgresql+asyncpg://x',
        )
        assert settings.chat_messages_per_hour == 20
        assert settings.chat_rate_limit_window_seconds == 3600

    def test_custom(self) -> None:
        settings = Settings(
            _env_file=None,
            widget_api_key='test-key-1234',
            admin_api_key='test-key-1234',
            anthropic_api_key='sk-ant-test',
            database_url='postgresql+asyncpg://x',
            chat_messages_per_hour=5,
            chat_rate_limit_window_seconds=60,
        )
        assert settings.chat_messages_per_hour == 5
        assert settings.chat_rate_limit_window_seconds == 60
