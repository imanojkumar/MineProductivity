"""Tests for mineproductivity.optimization.abstractions."""

from __future__ import annotations

from mineproductivity.kpis import KPIResult
from mineproductivity.optimization.abstractions import OptimizationContext, OptimizationModel


class TestOptimizationModel:
    def test_carries_no_shared_abstract_solve_method(self) -> None:
        """Design spec §8: each category base declares its own."""
        assert OptimizationModel.__abstractmethods__ == frozenset()
        for name in ("_solve_lp", "_solve_mip", "_solve_cp", "_solve_pareto", "_iterate"):
            assert not hasattr(OptimizationModel, name)

    def test_declares_only_the_meta_slot(self) -> None:
        assert set(getattr(OptimizationModel, "__annotations__", {})) == {"meta"}


class TestOptimizationContext:
    def test_evidence_defaults(self) -> None:
        context = OptimizationContext()
        assert context.kpi_results == ()
        assert context.analytics_results == ()
        assert context.decision_results == ()
        assert context.twin_snapshot is None
        assert context.simulation_results == ()

    def test_sequences_are_coerced_to_tuples(self) -> None:
        context = OptimizationContext(kpi_results=[KPIResult(code="UTIL.OEE", value=0.83, unit="")])
        assert isinstance(context.kpi_results, tuple)
        assert "OptimizationContext" in repr(context)
