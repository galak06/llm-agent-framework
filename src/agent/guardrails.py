from __future__ import annotations

import re

import structlog

from src.core.config import Settings
from src.domain.schemas import GuardrailResult

logger = structlog.get_logger()


class GuardrailEngine:
    """Pattern-based input/output guardrails. Patterns injected from config."""

    def __init__(self, settings: Settings) -> None:
        self._injection_patterns = [
            re.compile(re.escape(p), re.IGNORECASE) for p in settings.injection_patterns
        ]
        self._forbidden_output_patterns = [
            re.compile(re.escape(p), re.IGNORECASE) for p in settings.forbidden_output_patterns
        ]

    def check_input(self, text: str) -> GuardrailResult:
        """Check user input for injection attempts."""
        for pattern in self._injection_patterns:
            if pattern.search(text):
                logger.warning(
                    'guardrail.input_blocked',
                    pattern=pattern.pattern,
                )
                return GuardrailResult(
                    passed=False,
                    reason=f'Input matched injection pattern: {pattern.pattern}',
                )
        return GuardrailResult(passed=True)

    def check_output(self, text: str) -> GuardrailResult:
        """Check agent output for forbidden content."""
        for pattern in self._forbidden_output_patterns:
            if pattern.search(text):
                logger.warning(
                    'guardrail.output_blocked',
                    pattern=pattern.pattern,
                )
                return GuardrailResult(
                    passed=False,
                    reason=f'Output matched forbidden pattern: {pattern.pattern}',
                )
        return GuardrailResult(passed=True)
