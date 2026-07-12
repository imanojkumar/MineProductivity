"""Tests for mineproductivity.simulation.abstractions."""

from __future__ import annotations

from mineproductivity.decision import DecisionResult
from mineproductivity.kpis import KPIResult
from mineproductivity.simulation.abstractions import SimulationContext, SimulationModel


class _FakeStore:
    """Duck-typed ``EventStore`` stand-in, mirroring every sibling
    package's own doctest/test precedent."""


class TestSimulationModel:
    def test_carries_no_shared_abstract_execution_method(self) -> None:
        """Design spec §8: Monte Carlo, discrete-event, and
        system-dynamics execution are structurally different enough
        that each category base declares its own abstract method."""
        assert SimulationModel.__abstractmethods__ == frozenset()
        assert not hasattr(SimulationModel, "_trial")
        assert not hasattr(SimulationModel, "_advance")
        assert not hasattr(SimulationModel, "_step")

    def test_declares_only_the_meta_slot(self) -> None:
        annotations = getattr(SimulationModel, "__annotations__", {})
        assert set(annotations) == {"meta"}


class TestSimulationContext:
    def test_evidence_defaults_to_empty_tuples(self) -> None:
        context = SimulationContext(event_store=_FakeStore())
        assert context.kpi_results == ()
        assert context.analytics_results == ()
        assert context.decision_results == ()

    def test_evidence_sequences_are_coerced_to_tuples(self) -> None:
        context = SimulationContext(
            event_store=_FakeStore(),
            kpi_results=[KPIResult(code="UTIL.OEE", value=0.83, unit="")],
            decision_results=[DecisionResult(model_code="STRATEGY.Threshold")],
        )
        assert isinstance(context.kpi_results, tuple)
        assert context.kpi_results[0].code == "UTIL.OEE"
        assert isinstance(context.decision_results, tuple)

    def test_repr_names_the_collaborators(self) -> None:
        text = repr(SimulationContext(event_store=_FakeStore()))
        assert "SimulationContext" in text
        assert "kpi_results" in text
