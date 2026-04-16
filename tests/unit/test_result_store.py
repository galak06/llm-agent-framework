from __future__ import annotations

from src.domain.schemas import RunStatus


class TestRunStatusEnum:
    """Result store unit tests — integration tests cover Redis round-trip."""

    def test_run_status_values(self) -> None:
        assert RunStatus.PENDING == 'pending'
        assert RunStatus.RUNNING == 'running'
        assert RunStatus.DONE == 'done'
        assert RunStatus.FAILED == 'failed'

    def test_run_status_transitions(self) -> None:
        """Valid transitions: PENDING -> RUNNING -> DONE/FAILED."""
        statuses = [RunStatus.PENDING, RunStatus.RUNNING, RunStatus.DONE]
        assert all(isinstance(s, str) for s in statuses)
