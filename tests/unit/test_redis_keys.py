from __future__ import annotations

from src.core.config import Settings
from src.core.redis_keys import prefixed_key


def test_prefixed_key_empty_prefix_returns_plain_key() -> None:
    assert prefixed_key('', 'session', 'abc') == 'session:abc'
    assert prefixed_key('', 'runs', 'uuid-1') == 'runs:uuid-1'


def test_prefixed_key_with_prefix_scopes_key() -> None:
    assert prefixed_key('nalla', 'session', 'abc') == 'nalla:session:abc'


def test_prefixed_key_multiple_parts() -> None:
    assert (
        prefixed_key('cookbot', 'answer_cache', 'widget', 'hash123')
        == 'cookbot:answer_cache:widget:hash123'
    )


def test_redis_key_prefix_defaults_to_empty() -> None:
    settings = Settings(
        _env_file=None,
        widget_api_key='test-key-1234',
        admin_api_key='test-key-1234',
        anthropic_api_key='sk-ant-test',
        database_url='postgresql+asyncpg://x',
    )
    assert settings.redis_key_prefix == ''


def test_redis_key_prefix_from_env(monkeypatch: object) -> None:
    settings = Settings(
        _env_file=None,
        widget_api_key='test-key-1234',
        admin_api_key='test-key-1234',
        anthropic_api_key='sk-ant-test',
        database_url='postgresql+asyncpg://x',
        redis_key_prefix='nalla',
    )
    assert settings.redis_key_prefix == 'nalla'
