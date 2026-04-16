from __future__ import annotations

from src.jobs.worker import celery_app


@celery_app.task(bind=True, max_retries=3)
def run_agent_task(self, request_dict: dict, run_id: str) -> None:  # type: ignore[no-untyped-def]
    """
    Execute agent loop asynchronously.
    Writes status updates to RunResultStore throughout execution.
    Retries on transient failures (network, rate limit).
    """
    raise NotImplementedError
