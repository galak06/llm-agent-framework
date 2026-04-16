from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.schemas import ToolResult


@runtime_checkable
class BaseTool(Protocol):
    name: str
    version: str  # semver e.g. '1.0.0'
    description: str

    def get_schema(self) -> dict: ...

    async def execute(self, **kwargs: object) -> ToolResult: ...

    @property
    def versioned_name(self) -> str:
        """Returns 'tool_name@1.0.0' for logging."""
        return f'{self.name}@{self.version}'
