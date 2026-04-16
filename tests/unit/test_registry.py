from __future__ import annotations

import pytest

from src.core.exceptions import ToolNotFoundError
from src.tools.registry import ToolRegistry


class FakeTool:
    name = 'fake_tool'
    version = '1.0.0'
    description = 'A fake tool for testing'

    def get_schema(self) -> dict:
        return {'name': self.name, 'description': self.description}

    async def execute(self, **kwargs: object):  # type: ignore[no-untyped-def]
        from src.domain.schemas import ToolResult

        return ToolResult(tool_name=self.name, output='fake result')

    @property
    def versioned_name(self) -> str:
        return f'{self.name}@{self.version}'


class TestToolRegistry:
    def test_register_and_get(self) -> None:
        registry = ToolRegistry()
        tool = FakeTool()
        registry.register(tool)
        assert registry.get('fake_tool') is tool

    def test_get_missing_raises(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(ToolNotFoundError):
            registry.get('nonexistent')

    def test_list_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(FakeTool())
        tools = registry.list_tools()
        assert len(tools) == 1

    def test_get_schemas(self) -> None:
        registry = ToolRegistry()
        registry.register(FakeTool())
        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]['name'] == 'fake_tool'

    @pytest.mark.asyncio
    async def test_execute_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(FakeTool())
        result = await registry.execute_tool('fake_tool')
        assert result.output == 'fake result'
