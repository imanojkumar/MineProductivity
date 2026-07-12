"""Tests for mineproductivity.visualization.theme (design spec §21)."""

from __future__ import annotations

import pytest

from mineproductivity.visualization.exceptions import VisualizationValidationError
from mineproductivity.visualization.theme import Theme


class TestTheme:
    def test_defaults(self) -> None:
        theme = Theme(code="DARK_HIGH_CONTRAST")
        assert dict(theme.palette) == {}
        assert dict(theme.typography) == {}

    def test_empty_code_raises(self) -> None:
        with pytest.raises(VisualizationValidationError, match="code"):
            Theme(code="  ")

    def test_mappings_are_frozen_and_copied(self) -> None:
        palette = {"background": "#000"}
        theme = Theme(code="DARK", palette=palette)
        palette["background"] = "#fff"
        assert theme.palette["background"] == "#000"
        with pytest.raises(TypeError):
            theme.typography["body"] = "sans"  # type: ignore[index]

    def test_no_registry_exists_for_theme(self) -> None:
        """Design spec §21, §32: plain configuration data, never
        looked up polymorphically."""
        import mineproductivity.visualization._registry as registry_module

        registries = {
            name for name in dir(registry_module) if name.isupper() and not name.startswith("_")
        }
        assert registries == {"REGISTRY", "RENDERERS"}
