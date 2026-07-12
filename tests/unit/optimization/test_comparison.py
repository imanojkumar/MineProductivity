"""Tests for mineproductivity.optimization.comparison."""

from __future__ import annotations

import pytest

from mineproductivity.analytics import StatisticalSummary
from mineproductivity.optimization import comparison as comparison_module
from mineproductivity.optimization.comparison import PlanComparator
from mineproductivity.optimization.exceptions import OptimizationValidationError
from mineproductivity.optimization.result import OptimizationResult


def _results(*values: float) -> list[OptimizationResult]:
    return [
        OptimizationResult(objective_value=value, solution={"trucks": value / 10.0})
        for value in values
    ]


class TestCompare:
    def test_summarizes_objective_values_per_problem(self) -> None:
        summaries = PlanComparator().compare(
            {"baseline": _results(10.0, 20.0, 30.0), "surge": _results(40.0, 60.0)}
        )
        assert isinstance(summaries["baseline"], StatisticalSummary)
        assert summaries["baseline"].mean == 20.0
        assert summaries["surge"].mean == 50.0

    def test_named_solution_variable_extraction(self) -> None:
        summaries = PlanComparator().compare({"only": _results(10.0, 30.0)}, variable="trucks")
        assert summaries["only"].mean == 2.0

    def test_delegates_to_analytics_describe(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Design spec §35's delegation proof."""
        calls: list[int] = []
        real_describe = comparison_module.describe

        def _spy(series: object) -> StatisticalSummary:
            calls.append(1)
            return real_describe(series)  # type: ignore[arg-type]

        monkeypatch.setattr(comparison_module, "describe", _spy)
        PlanComparator().compare({"only": _results(1.0, 2.0)})
        assert calls == [1]

    def test_zero_results_raises(self) -> None:
        with pytest.raises(OptimizationValidationError, match="zero results"):
            PlanComparator().compare({"empty": []})

    def test_no_numeric_values_raises(self) -> None:
        with pytest.raises(OptimizationValidationError, match="objective_value"):
            PlanComparator().compare({"only": [OptimizationResult(feasible=False)]})

    def test_repr(self) -> None:
        assert repr(PlanComparator()) == "PlanComparator()"
