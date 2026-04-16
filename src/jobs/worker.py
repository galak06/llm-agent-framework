from __future__ import annotations

from celery import Celery

from src.core.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery(
        'llm_agent_framework',
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )
    app.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
    )
    app.autodiscover_tasks(['src.jobs'])
    return app


celery_app = create_celery_app()
