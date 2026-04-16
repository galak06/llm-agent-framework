from __future__ import annotations

from src.domain.schemas import ToolResult
from src.tools.base import BaseTool


class MockTool:
    """A mock tool for testing the BaseTool protocol."""

    name = 'mock_tool'
    version = '1.0.0'
    description = 'A mock tool for testing'

    @property
    def versioned_name(self) -> str:
        return f'{self.name}@{self.version}'

    def get_schema(self) -> dict[str, object]:
        return {
            'name': self.name,
            'description': self.description,
            'input_schema': {'type': 'object', 'properties': {}},
        }

    async def execute(self, **kwargs: object) -> ToolResult:
        return ToolResult(tool_name=self.name, output='mock result')


class TestToolProtocol:
    def test_tool_has_protocol_methods(self) -> None:
        tool = MockTool()
        assert hasattr(tool, 'get_schema')
        assert hasattr(tool, 'execute')
        assert hasattr(tool, 'versioned_name')

    def test_versioned_name_format(self) -> None:
        tool = MockTool()
        assert tool.versioned_name == 'mock_tool@1.0.0'

    def test_tool_has_required_fields(self) -> None:
        tool = MockTool()
        assert tool.name
        assert tool.version
        assert tool.description

    def test_get_schema_returns_dict(self) -> None:
        tool = MockTool()
        schema = tool.get_schema()
        assert 'name' in schema
        assert 'input_schema' in schema
