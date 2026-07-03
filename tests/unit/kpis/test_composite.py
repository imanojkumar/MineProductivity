"""Tests for mineproductivity.kpis.composite."""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

import pytest

from mineproductivity.kpis.composite import CompositeKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata
from mineproductivity.kpis.result import KPIResult


class _ProductCompositeKPI(CompositeKPI):
    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="UTIL.ProductFixture",
        name="Product Fixture",
        official_name="Product Fixture",
        business_purpose="x",
        operational_question="x",
        business_meaning="x",
        formula="A * B",
        unit="ratio",
        dimensions=("Shift",),
        required_events=("MAINTENANCE",),
        dependencies=("A", "B"),
        aggregation=Aggregation.DERIVED,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L1_MANUAL,
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
    )

    def _combine(self, component_results: Mapping[str, KPIResult]) -> float | None:
        return component_results["A"].value * component_results["B"].value  # type: ignore[operator]


class TestCompositeKPIIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            CompositeKPI()  # type: ignore[abstract]


class TestComputeRaisesByDesign:
    def test_compute_raises_not_implemented(self) -> None:
        kpi = _ProductCompositeKPI()
        with pytest.raises(NotImplementedError, match="CompositeKPI uses _combine"):
            kpi._compute([])


class TestCombineHappyPath:
    def test_combines_component_results(self) -> None:
        kpi = _ProductCompositeKPI()
        component_results = {
            "A": KPIResult(code="A", value=0.9, unit="ratio", n=10),
            "B": KPIResult(code="B", value=0.8, unit="ratio", n=5),
        }
        result = kpi.combine(component_results)
        assert result.value == pytest.approx(0.72)
        assert result.code == "UTIL.ProductFixture"
        assert result.n == 15
        assert result.warnings == ()


class TestCombineNonePropagation:
    def test_one_none_component_propagates_none_never_a_fabricated_zero(self) -> None:
        kpi = _ProductCompositeKPI()
        component_results = {
            "A": KPIResult(code="A", value=None, unit="ratio", warnings=("no data",)),
            "B": KPIResult(code="B", value=0.8, unit="ratio"),
        }
        result = kpi.combine(component_results)
        assert result.value is None
        assert "A" in result.warnings[0]

    def test_all_none_components_propagate_none(self) -> None:
        kpi = _ProductCompositeKPI()
        component_results = {
            "A": KPIResult(code="A", value=None, unit="ratio"),
            "B": KPIResult(code="B", value=None, unit="ratio"),
        }
        result = kpi.combine(component_results)
        assert result.value is None
        assert "A" in result.warnings[0]
        assert "B" in result.warnings[0]
