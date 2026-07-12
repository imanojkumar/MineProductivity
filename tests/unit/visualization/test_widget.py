"""Tests for mineproductivity.visualization.widget (design spec §10)."""

from __future__ import annotations

import pytest

from mineproductivity.core.serialization import to_dict
from mineproductivity.visualization.exceptions import VisualizationValidationError
from mineproductivity.visualization.widget import Widget


def _widget(**overrides: object) -> Widget:
    kwargs: dict[str, object] = {
        "code": "tph_card",
        "visualization_code": "KPI_CARD.Standard",
        "binding": {"kpi_code": "PROD.TPH"},
    }
    kwargs.update(overrides)
    return Widget(**kwargs)  # type: ignore[arg-type]


class TestWidget:
    def test_empty_code_raises(self) -> None:
        with pytest.raises(VisualizationValidationError, match="code"):
            _widget(code=" ")

    def test_empty_visualization_code_raises(self) -> None:
        with pytest.raises(VisualizationValidationError, match="visualization_code"):
            _widget(visualization_code="")

    def test_binding_defaults_empty_and_is_frozen(self) -> None:
        widget = _widget(binding={})
        assert dict(widget.binding) == {}
        with pytest.raises(TypeError):
            _widget().binding["kpi_code"] = "OTHER"  # type: ignore[index]

    def test_binding_is_copied_not_aliased(self) -> None:
        binding = {"kpi_code": "PROD.TPH"}
        widget = _widget(binding=binding)
        binding["kpi_code"] = "OTHER"
        assert widget.binding["kpi_code"] == "PROD.TPH"

    def test_serializes_via_core_serialization(self) -> None:
        serialized = to_dict(_widget())
        assert serialized["visualization_code"] == "KPI_CARD.Standard"
        assert serialized["binding"] == {"kpi_code": "PROD.TPH"}
