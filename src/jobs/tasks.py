from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog

from src.jobs.worker import celery_app

logger = structlog.get_logger()


async def _execute_agent(request_dict: dict[str, str], run_id: str) -> None:
    """Async inner function that runs the agent orchestrator."""
    from src.core.config import get_settings
    from src.core.container import ServiceContainer
    from src.core.exceptions import GuardrailViolationError, TokenBudgetExceededError
    from src.domain.schemas import RunStatus, RunStatusResponse

    settings = get_settings()
    container = ServiceContainer(settings)
    now = datetime.now(UTC)

    try:
        await container.result_store.set_status(run_id, RunStatus.RUNNING)

        orchestrator = container.build_orchestrator()

        result = await orchestrator.run(
            user_id=request_dict['user_id'],
            session_id=request_dict['session_id'],
            message=request_dict['message'],
        )

        await container.result_store.set_result(
            run_id,
            RunStatusResponse(
                run_id=run_id,
                status=RunStatus.DONE,
                answer=result.answer,
                tools_used=result.tools_used,
                total_tokens=result.total_tokens,
                created_at=now,
            ),
        )
        logger.info('task.completed', run_id=run_id, tools_used=result.tools_used)

    except (GuardrailViolationError, TokenBudgetExceededError) as exc:
        logger.warning('task.rejected', run_id=run_id, error=str(exc))
        await container.result_store.set_result(
            run_id,
            RunStatusResponse(
                run_id=run_id,
                status=RunStatus.FAILED,
                error=str(exc),
                created_at=now,
            ),
        )

    except Exception as exc:
        logger.error('task.failed', run_id=run_id, error=str(exc))
        await container.result_store.set_result(
            run_id,
            RunStatusResponse(
                run_id=run_id,
                status=RunStatus.FAILED,
                error=f'Internal error: {type(exc).__name__}',
                created_at=now,
            ),
        )
        raise


@celery_app.task(bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def run_agent_task(self: Any, request_dict: dict[str, str], run_id: str) -> None:
    """
    Execute agent loop asynchronously.
    Writes status updates to RunResultStore throughout execution.
    Retries on transient failures (network, rate limit).
    """
    try:
        asyncio.run(_execute_agent(request_dict, run_id))
    except Exception as exc:
        import anthropic

        if isinstance(exc, (anthropic.RateLimitError, anthropic.APIConnectionError)):
            logger.warning(
                'task.retry',
                run_id=run_id,
                attempt=self.request.retries + 1,
                error=str(exc),
            )
            raise self.retry(exc=exc, countdown=2**self.request.retries * 10) from exc
        raise
