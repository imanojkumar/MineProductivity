"""Tests for mineproductivity.kpis.base_kpi."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

import pytest

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata


class _SumKPI(BaseKPI):
    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="PROD.SumFixture",
        name="Sum Fixture",
        official_name="Sum Fixture",
        business_purpose="x",
        operational_question="x",
        business_meaning="x",
        formula="sum(value)",
        unit="t",
        dimensions=("Shift",),
        required_events=("CYCLE",),
        aggregation=Aggregation.ADDITIVE,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L1_MANUAL,
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("value",)

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        return sum(row["value"] for row in rows)


class _NoRequiredColumnsKPI(BaseKPI):
    meta: ClassVar[KPIMetadata] = _SumKPI.meta.replace(code="PROD.NoRequiredColumnsFixture")

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        return float(len(rows))


class TestBaseKPIIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseKPI()  # type: ignore[abstract]


class TestRequiredColumnsDefault:
    def test_default_required_columns_is_empty(self) -> None:
        kpi = _NoRequiredColumnsKPI()
        assert kpi._required_columns() == ()

    def test_no_required_columns_means_no_precheck(self) -> None:
        kpi = _NoRequiredColumnsKPI()
        result = kpi.compute([{"anything": 1}, {"anything": 2}])
        assert result.value == 2.0
        assert result.warnings == ()


class TestComputeHappyPath:
    def test_wraps_compute_result_in_a_kpi_result(self) -> None:
        kpi = _SumKPI()
        result = kpi.compute([{"value": 10.0}, {"value": 5.0}])
        assert result.code == "PROD.SumFixture"
        assert result.value == 15.0
        assert result.unit == "t"
        assert result.n == 2
        assert result.warnings == ()

    def test_empty_rows(self) -> None:
        kpi = _SumKPI()
        result = kpi.compute([])
        assert result.value == 0
        assert result.n == 0


class TestComputeMissingColumns:
    def test_missing_column_on_every_row_produces_a_warning_never_an_exception(self) -> None:
        kpi = _SumKPI()
        result = kpi.compute([{"not_value": 1}])
        assert result.value is None
        assert "missing required columns" in result.warnings[0]
        assert "value" in result.warnings[0]

    def test_missing_column_on_only_some_rows_still_warns(self) -> None:
        kpi = _SumKPI()
        result = kpi.compute([{"value": 1.0}, {"not_value": 2.0}])
        assert result.value is None
        assert result.warnings

    def test_n_reflects_row_count_even_when_uncomputable(self) -> None:
        kpi = _SumKPI()
        result = kpi.compute([{"not_value": 1}, {"not_value": 2}, {"not_value": 3}])
        assert result.n == 3


class TestComputeIsStateless:
    def test_same_instance_reused_across_calls_with_different_rows(self) -> None:
        kpi = _SumKPI()
        first = kpi.compute([{"value": 1.0}])
        second = kpi.compute([{"value": 100.0}])
        assert first.value == 1.0
        assert second.value == 100.0
