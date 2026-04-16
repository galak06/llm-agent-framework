from __future__ import annotations

import structlog
from langfuse import Langfuse

from src.core.config import Settings


def configure_logging(settings: Settings) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.JSONRenderer(),
        ],
    )


def get_langfuse(settings: Settings) -> Langfuse | None:
    if not settings.langfuse_public_key:
        return None
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key.get_secret_value(),
        host=settings.langfuse_host,
    )
