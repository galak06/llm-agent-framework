from __future__ import annotations

from src.jobs.worker import celery_app


@celery_app.task(bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def run_agent_task(self: object, request_dict: dict[str, str], run_id: str) -> None:
    """
    Execute agent loop asynchronously.
    Writes status updates to RunResultStore throughout execution.
    Retries on transient failures (network, rate limit).
    """
    raise NotImplementedError
