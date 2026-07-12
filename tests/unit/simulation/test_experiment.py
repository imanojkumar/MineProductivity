"""Tests for mineproductivity.simulation.experiment."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from mineproductivity.core import BaseValueObject, InMemoryRepository
from mineproductivity.simulation._registry import register
from mineproductivity.simulation.abstractions import SimulationContext
from mineproductivity.simulation.clock import SimulationClock, TimeProgressionMode
from mineproductivity.simulation.executor import SimulationExecutor
from mineproductivity.simulation.experiment import Experiment, ExperimentRunner
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.montecarlo import MonteCarloModel
from mineproductivity.simulation.result import SimulationResult
from mineproductivity.simulation.run import RunStatus, SimulationRun
from mineproductivity.simulation.scenario import Scenario
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


@register
class _SeedEchoModel(MonteCarloModel):
    meta = SimulationMetadata(
        code="MONTECARLO.ExperimentSeedEcho",
        category=SimulationCategory.MONTE_CARLO,
        description="Echoes the supplied seed into the trial outcome.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        outcome = random.Random(random_seed).uniform(0.0, 100.0)
        return SimulationResult(
            final_state=SimulationState(
                attributes={"outcome": outcome, "seed": random_seed}, simulated_time=_EPOCH
            )
        )


class _FakeStore: ...


def _scenario(**overrides: object) -> Scenario:
    fields: dict[str, object] = {
        "code": "TEST.ExperimentScenario",
        "model_code": "MONTECARLO.ExperimentSeedEcho",
        "time_horizon": timedelta(hours=12),
    }
    fields.update(overrides)
    return Scenario(**fields)  # type: ignore[arg-type]


def _runner() -> tuple[InMemoryRepository[SimulationRun, str], ExperimentRunner]:
    repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    executor = SimulationExecutor(
        repository=repository, clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED)
    )
    return repository, ExperimentRunner(executor=executor, repository=repository)


class TestExperiment:
    def test_is_a_frozen_value_object(self) -> None:
        assert issubclass(Experiment, BaseValueObject)

    def test_carries_name_scenario_and_ordered_run_ids(self) -> None:
        experiment = Experiment(name="surge", scenario=_scenario(), run_ids=("RUN-1", "RUN-2"))
        assert experiment.run_ids == ("RUN-1", "RUN-2")


class TestRunTrials:
    def test_runs_every_trial_and_preserves_trial_order(self) -> None:
        repository, runner = _runner()
        experiment = runner.run_trials(
            _scenario(), trials=8, context=SimulationContext(event_store=_FakeStore())
        )
        assert len(experiment.run_ids) == 8
        for index, run_id in enumerate(experiment.run_ids):
            run = repository.get(run_id)
            assert run.status is RunStatus.COMPLETED
            assert run.state.attributes["seed"] == index  # distinct seed per trial (§13)
        assert f"trial-{0:04d}" in experiment.run_ids[0]

    def test_each_trial_gets_a_distinct_seed_hence_distinct_outcomes(self) -> None:
        repository, runner = _runner()
        experiment = runner.run_trials(
            _scenario(), trials=5, context=SimulationContext(event_store=_FakeStore())
        )
        outcomes = {
            repository.get(run_id).state.attributes["outcome"] for run_id in experiment.run_ids
        }
        assert len(outcomes) == 5

    def test_rerunning_the_same_scenario_never_collides_on_run_ids(self) -> None:
        repository, runner = _runner()
        context = SimulationContext(event_store=_FakeStore())
        first = runner.run_trials(_scenario(), trials=2, context=context)
        second = runner.run_trials(_scenario(), trials=2, context=context)
        assert set(first.run_ids).isdisjoint(second.run_ids)
        assert len(repository.list()) == 4

    def test_zero_trials_returns_an_empty_experiment_never_raises(self) -> None:
        """Design spec §28: a legitimately incomplete input."""
        repository, runner = _runner()
        experiment = runner.run_trials(
            _scenario(), trials=0, context=SimulationContext(event_store=_FakeStore())
        )
        assert experiment.run_ids == ()
        assert repository.list() == []

    def test_experiment_name_carries_scenario_code_and_version(self) -> None:
        _, runner = _runner()
        experiment = runner.run_trials(
            _scenario(), trials=1, context=SimulationContext(event_store=_FakeStore())
        )
        assert experiment.name == "TEST.ExperimentScenario@1.0.0"

    def test_repr_names_the_collaborators(self) -> None:
        _, runner = _runner()
        assert "ExperimentRunner" in repr(runner)
