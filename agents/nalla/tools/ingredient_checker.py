from src.domain.schemas import ToolResult


class IngredientCheckerTool:
    name = 'check_ingredient'
    version = '1.0.0'
    description = 'Check if a food ingredient is safe for dogs'

    def get_schema(self) -> dict:
        raise NotImplementedError

    async def execute(self, **kwargs: object) -> ToolResult:
        raise NotImplementedError
