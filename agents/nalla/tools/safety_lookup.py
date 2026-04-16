from src.domain.schemas import ToolResult


class SafetyLookupTool:
    name = 'safety_lookup'
    version = '1.0.0'
    description = 'Look up safety information for a given substance'

    def get_schema(self) -> dict:
        raise NotImplementedError

    async def execute(self, **kwargs: object) -> ToolResult:
        raise NotImplementedError
