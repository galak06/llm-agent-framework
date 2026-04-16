from __future__ import annotations

import structlog

from src.core.exceptions import ToolNotFoundError
from src.domain.schemas import ToolResult
from src.tools.base import BaseTool

logger = structlog.get_logger()


class ToolRegistry:
    """Registry for discovering and executing versioned tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        logger.info('tool.register', tool=tool.versioned_name)
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f'Tool not found: {name}')
        return tool

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_schemas(self) -> list[dict]:
        return [tool.get_schema() for tool in self._tools.values()]

    async def execute_tool(self, name: str, **kwargs: object) -> ToolResult:
        tool = self.get(name)
        logger.info('tool.execute', tool=tool.versioned_name, kwargs=kwargs)
        result = await tool.execute(**kwargs)
        logger.info('tool.result', tool=tool.versioned_name, error=result.error)
        return result
