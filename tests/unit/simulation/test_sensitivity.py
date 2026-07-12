"""Tests for mineproductivity.simulation.sensitivity."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.analytics import ConfidenceInterval, DistributionSummary
from mineproductivity.core import InMemoryRepository
from mineproductivity.simulation import sensitivity as sensitivity_module
from mineproductivity.simulation._registry import register
from mineproductivity.simulation.abstractions import SimulationContext
from mineproductivity.simulation.clock import SimulationClock, TimeProgressionMode
from mineproductivity.simulation.executor import SimulationExecutor
from mineproductivity.simulation.experiment import ExperimentRunner
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.montecarlo import MonteCarloModel
from mineproductivity.simulation.result import SimulationResult
from mineproductivity.simulation.run import SimulationRun
from mineproductivity.simulation.scenario import Scenario, ScenarioStatus, published_scenario
from mineproductivity.simulation.sensitivity import SensitivityAnalyzer
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


@register
class _ParameterEchoModel(MonteCarloModel):
    meta = SimulationMetadata(
        code="MONTECARLO.SensitivityParamEcho",
        category=SimulationCategory.MONTE_CARLO,
        description="Echoes the swept parameter into the trial outcome.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        trucks = int(scenario.parameters.get("trucks_added", 0))
        return SimulationResult(
            final_state=SimulationState(attributes={"trucks_added": trucks}, simulated_time=_EPOCH)
        )


class _FakeStore: ...


def _scenario() -> Scenario:
    return Scenario(
        code="TEST.SensitivityScenario",
        model_code="MONTECARLO.SensitivityParamEcho",
        parameters={"trucks_added": 0},
        time_horizon=timedelta(hours=12),
    )


def _analyzer() -> tuple[InMemoryRepository[SimulationRun, str], SensitivityAnalyzer]:
    repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    executor = SimulationExecutor(
        repository=repository, clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED)
    )
    runner = ExperimentRunner(executor=executor, repository=repository)
    return repository, SensitivityAnalyzer(runner=runner)


class TestSweep:
    def test_one_run_per_value_ordered_to_match_values(self) -> None:
        """Design spec §20: run_ids ordered to match values' order, so
        a caller can zip them back together."""
        repository, analyzer = _analyzer()
        values = [1, 2, 3]
        experiment = analyzer.sweep(
            _scenario(),
            parameter="trucks_added",
            values=values,
            context=SimulationContext(event_store=_FakeStore()),
        )
        assert len(experiment.run_ids) == 3
        observed = [
            repository.get(run_id).state.attributes["trucks_added"] for run_id in experiment.run_ids
        ]
        assert observed == values

    def test_the_base_scenario_is_never_edited_in_place_or_published(self) -> None:
        """Design spec §9, §34: swept variants are transient copies of
        the frozen ``Scenario``; the governed artifact is untouched."""
        _, analyzer = _analyzer()
        base = _scenario()
        analyzer.sweep(
            base,
            parameter="trucks_added",
            values=[5],
            context=SimulationContext(event_store=_FakeStore()),
        )
        assert dict(base.parameters) == {"trucks_added": 0}
        assert base.status is ScenarioStatus.PROPOSED
        assert published_scenario(base.code) is None

    def test_the_experiment_names_the_swept_parameter(self) -> None:
        _, analyzer = _analyzer()
        experiment = analyzer.sweep(
            _scenario(),
            parameter="trucks_added",
            values=[1],
            context=SimulationContext(event_store=_FakeStore()),
        )
        assert experiment.name == "TEST.SensitivityScenario::sweep(trucks_added)"
        assert experiment.scenario == _scenario()

    def test_zero_values_returns_an_empty_experiment_never_raises(self) -> None:
        _, analyzer = _analyzer()
        experiment = analyzer.sweep(
            _scenario(),
            parameter="trucks_added",
            values=[],
            context=SimulationContext(event_store=_FakeStore()),
        )
        assert experiment.run_ids == ()


class TestSummarize:
    def test_hands_outcomes_to_analytics_distribution_and_confidence_interval(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Design spec §35's delegation proof: assert the actual
        ``analytics`` primitives invoked."""
        invoked: list[str] = []
        real_distribution = sensitivity_module.distribution
        real_interval = sensitivity_module.confidence_interval

        def _spy_distribution(values: object) -> DistributionSummary:
            invoked.append("distribution")
            return real_distribution(values)  # type: ignore[arg-type]

        def _spy_interval(values: object, *, confidence: float = 0.95) -> ConfidenceInterval:
            invoked.append("confidence_interval")
            return real_interval(values, confidence=confidence)  # type: ignore[arg-type]

        monkeypatch.setattr(sensitivity_module, "distribution", _spy_distribution)
        monkeypatch.setattr(sensitivity_module, "confidence_interval", _spy_interval)

        _, analyzer = _analyzer()
        shape, interval = analyzer.summarize([10.0, 12.0, 11.0, 13.0], confidence=0.9)
        assert invoked == ["distribution", "confidence_interval"]
        assert isinstance(shape, DistributionSummary)
        assert isinstance(interval, ConfidenceInterval)
        assert interval.confidence == 0.9

    def test_repr(self) -> None:
        _, analyzer = _analyzer()
        assert "SensitivityAnalyzer" in repr(analyzer)
