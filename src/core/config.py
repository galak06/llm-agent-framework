from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        hide_input_in_errors=True,
    )

    # App
    app_name: str = 'LLM Agent Framework'
    app_env: str = 'development'
    debug: bool = False
    cors_origins: list[str] = Field(default_factory=list)
    api_version: str = 'v1'

    # Security
    widget_api_key: str
    admin_api_key: str
    allowed_input_max_length: int = 500

    # LLM
    anthropic_api_key: str
    llm_model: str = 'claude-sonnet-4-20250514'
    llm_max_tokens: int = 4096
    agent_max_iterations: int = 5
    agent_token_budget_daily: int = 50_000
    memory_top_k: int = 3

    # Async Jobs
    celery_broker_url: str = 'redis://localhost:6379/1'
    celery_result_backend: str = 'redis://localhost:6379/2'
    run_result_ttl_seconds: int = 3600

    # Database
    database_url: str
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Redis
    redis_url: str = 'redis://localhost:6379'
    session_ttl_seconds: int = 3600
    tool_cache_ttl_seconds: int = 86400

    # Rate Limiting
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60

    # Guardrails (domain-injected)
    injection_patterns: list[str] = Field(default_factory=list)
    forbidden_output_patterns: list[str] = Field(default_factory=list)

    # Persona (domain-injected)
    persona_name: str = 'Assistant'
    persona_system_prompt_key: str = 'system_base'
    fallback_message_key: str = 'fallback_default'
    agent_name: str = 'default'

    # Observability
    sentry_dsn: str = ''
    langfuse_public_key: str = ''
    langfuse_secret_key: str = ''
    langfuse_host: str = 'https://cloud.langfuse.com'
    log_level: str = 'INFO'


@lru_cache
def get_settings() -> Settings:
    return Settings()
