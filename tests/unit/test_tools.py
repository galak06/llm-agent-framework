from __future__ import annotations

from agents.nalla.tools.ingredient_checker import IngredientCheckerTool
from agents.nalla.tools.safety_lookup import SafetyLookupTool


class TestToolVersioning:
    def test_ingredient_checker_has_version(self) -> None:
        tool = IngredientCheckerTool()
        assert tool.version == '1.0.0'
        assert tool.name == 'check_ingredient'

    def test_safety_lookup_has_version(self) -> None:
        tool = SafetyLookupTool()
        assert tool.version == '1.0.0'
        assert tool.name == 'safety_lookup'

    def test_versioned_name_format(self) -> None:
        tool = IngredientCheckerTool()
        expected = f'{tool.name}@{tool.version}'
        assert expected == 'check_ingredient@1.0.0'

    def test_all_tools_have_description(self) -> None:
        for tool_cls in [IngredientCheckerTool, SafetyLookupTool]:
            tool = tool_cls()
            assert tool.description
            assert len(tool.description) > 0
