from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
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
    widget_api_key: str = Field(min_length=8)
    admin_api_key: str = Field(min_length=8)
    allowed_input_max_length: int = Field(default=500, gt=0, le=10000)

    # LLM
    llm_provider: str = 'anthropic'  # 'anthropic' or 'gemini'
    anthropic_api_key: str = ''
    gemini_api_key: str = ''
    llm_model: str = 'claude-sonnet-4-20250514'
    llm_max_tokens: int = Field(default=4096, gt=0, le=100000)
    agent_max_iterations: int = Field(default=5, gt=0, le=50)
    agent_token_budget_daily: int = Field(default=50_000, gt=0)
    memory_top_k: int = Field(default=3, gt=0, le=20)

    # Knowledge base mode — controls how external KB content reaches the LLM.
    #   'off'     — no KB injection (LLM relies on system prompt only).
    #   'context' — load a static markdown KB file and stuff it into the
    #               cached system prompt (best for small corpora <50 posts).
    #   'rag'     — embed the user query, retrieve top-K chunks from pgvector,
    #               inject them per-turn (use for large or growing corpora).
    kb_mode: str = 'off'
    kb_top_k: int = Field(default=5, gt=0, le=20)
    kb_context_file: str = ''  # e.g., 'agents/nalla/seeds/wp_kb.md'

    # Embeddings (Voyage AI) — only consulted when kb_mode='rag'.
    voyage_api_key: SecretStr = SecretStr('')
    voyage_model: str = 'voyage-3-large'
    voyage_embedding_dim: int = Field(default=1024, gt=0, le=4096)

    @field_validator('kb_mode')
    @classmethod
    def validate_kb_mode(cls, v: str) -> str:
        allowed = {'off', 'context', 'rag'}
        if v not in allowed:
            msg = f'kb_mode must be one of {allowed}, got {v!r}'
            raise ValueError(msg)
        return v

    # Async Jobs
    celery_broker_url: str = 'redis://localhost:6379/1'
    celery_result_backend: str = 'redis://localhost:6379/2'
    run_result_ttl_seconds: int = Field(default=3600, gt=0)

    # Database
    database_url: str = Field(min_length=1)
    db_pool_size: int = Field(default=5, gt=0, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=100)

    # Redis
    redis_password: SecretStr = SecretStr('')
    redis_url: str = 'redis://localhost:6379'
    session_ttl_seconds: int = Field(default=3600, gt=0)
    tool_cache_ttl_seconds: int = Field(default=86400, gt=0)
    # Multi-agent isolation: when set, prepended to every app-level Redis key
    # (sessions, rate limits, answer cache, run store). Set to the agent name
    # (e.g., 'nalla', 'cookbot') when running multiple agents on one Redis.
    redis_key_prefix: str = ''

    # Rate Limiting
    rate_limit_requests: int = Field(default=10, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)

    # Per-chatId message cap (anti-abuse: one visitor can't monopolize the LLM budget)
    chat_messages_per_hour: int = Field(default=20, gt=0)
    chat_rate_limit_window_seconds: int = Field(default=3600, gt=0)

    # Origin header allowlist for the public /prediction endpoint.
    # Empty list disables the check (dev default); list of origins enforces strict match.
    widget_allowed_origins: list[str] = Field(default_factory=list)

    # Answer cache — short-circuits repeated anonymous questions (cost-burn defense)
    answer_cache_enabled: bool = True
    answer_cache_ttl_seconds: int = Field(default=86400, gt=0)

    # Guardrails (domain-injected)
    injection_patterns: list[str] = Field(default_factory=list)
    forbidden_output_patterns: list[str] = Field(default_factory=list)

    # Image uploads
    image_max_bytes: int = Field(default=5 * 1024 * 1024, gt=0, le=20 * 1024 * 1024)
    image_max_per_request: int = Field(default=2, gt=0, le=10)
    image_allowed_mime_types: list[str] = Field(
        default_factory=lambda: ['image/jpeg', 'image/png', 'image/webp']
    )

    # Persona (domain-injected)
    persona_name: str = 'Assistant'
    persona_system_prompt_key: str = 'system_base'
    fallback_message_key: str = 'fallback_default'
    agent_name: str = 'default'

    # Observability
    sentry_dsn: str = ''
    langfuse_public_key: str = ''
    langfuse_secret_key: SecretStr = SecretStr('')
    langfuse_host: str = 'https://cloud.langfuse.com'
    log_level: str = 'INFO'

    @field_validator('app_env')
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {'development', 'staging', 'production', 'test'}
        if v not in allowed:
            msg = f'app_env must be one of {allowed}, got {v!r}'
            raise ValueError(msg)
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        upper = v.upper()
        if upper not in allowed:
            msg = f'log_level must be one of {allowed}, got {v!r}'
            raise ValueError(msg)
        return upper

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(('postgresql', 'sqlite')):
            msg = 'database_url must start with postgresql or sqlite'
            raise ValueError(msg)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
