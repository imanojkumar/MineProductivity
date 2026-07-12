"""Integration test reproducing design spec 09 §17's worked example
end-to-end: a 500-trial Monte Carlo experiment seeded from a real
``digital_twin.TwinSnapshot``, with trial outcomes summarized through
``analytics`` via ``ScenarioComparator`` -- nothing in ``simulation``
recomputes a twin's state or re-derives descriptive statistics."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from mineproductivity.core import InMemoryRepository
from mineproductivity.digital_twin import TwinSnapshot, TwinState, TwinStatus
from mineproductivity.events import AsOf
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.simulation import (
    ExperimentRunner,
    MonteCarloModel,
    RunStatus,
    Scenario,
    ScenarioComparator,
    SimulationCategory,
    SimulationClock,
    SimulationContext,
    SimulationExecutor,
    SimulationMetadata,
    SimulationResult,
    SimulationRun,
    SimulationState,
    TimeProgressionMode,
    register,
)

_NOW = datetime(2026, 7, 8, 6, 0, tzinfo=timezone.utc)


@register
class _HaulCycleVariability(MonteCarloModel):
    """Test-local flagship model: perturbs the snapshot-seeded fleet
    throughput by a seed-determined factor -- all randomness derives
    from the supplied ``random_seed`` (spec 09 §33)."""

    meta = SimulationMetadata(
        code="MONTECARLO.IntegrationHaulCycleVariability",
        category=SimulationCategory.MONTE_CARLO,
        description="Perturbs snapshot-seeded fleet throughput per trial.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        assert scenario.initial_state is not None
        baseline = float(scenario.initial_state.state.attributes["tonnes_per_hour"])
        trucks_added = int(scenario.parameters.get("trucks_added", 0))
        rng = random.Random(random_seed)
        projected = (baseline + trucks_added * 180.0) * rng.uniform(0.9, 1.1)
        return SimulationResult(
            final_state=SimulationState(
                attributes={"tonnes_per_hour": projected},
                simulated_time=_NOW + scenario.time_horizon,
            )
        )


def test_500_trial_monte_carlo_experiment_seeded_from_a_twin_snapshot() -> None:
    snapshot = TwinSnapshot(
        twin_id="FLEET-NORTH",
        state=TwinState(attributes={"tonnes_per_hour": 4200.0}, captured_at=_NOW),
        status=TwinStatus.SYNCHRONIZED,
        as_of=AsOf(utc=_NOW),
    )
    scenario = Scenario(
        code="FLEET.IntegrationNightShiftSurge",
        model_code="MONTECARLO.IntegrationHaulCycleVariability",
        parameters={"trucks_added": 3},
        time_horizon=timedelta(hours=12),
        initial_state=snapshot,
    )

    run_repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    executor = SimulationExecutor(
        repository=run_repository,
        clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED),
    )
    runner = ExperimentRunner(executor=executor, repository=run_repository)
    context = SimulationContext(event_store=_InMemoryEventStore())

    experiment = runner.run_trials(scenario, trials=500, context=context)
    assert len(experiment.run_ids) == 500

    results = [run_repository.get(run_id) for run_id in experiment.run_ids]
    assert all(run.status is RunStatus.COMPLETED for run in results)

    comparator = ScenarioComparator()
    summary = comparator.compare({"night_shift_surge": [run.state for run in results]})
    surge = summary["night_shift_surge"]
    assert surge.n == 500
    # 4200 + 3x180 = 4740 nominal, x U(0.9, 1.1): every trial in bounds,
    # the mean near nominal, and real spread across trials.
    assert 4740.0 * 0.9 <= surge.minimum <= surge.mean <= surge.maximum <= 4740.0 * 1.1
    assert surge.percentiles[90] > surge.percentiles[50]

    # Reproducibility (spec 09 §35): the same experiment re-run produces
    # the identical outcome multiset, because each trial's randomness
    # derives solely from its trial-index seed.
    rerun = runner.run_trials(scenario, trials=500, context=context)
    first_outcomes = sorted(
        float(run_repository.get(run_id).state.attributes["tonnes_per_hour"])
        for run_id in experiment.run_ids
    )
    second_outcomes = sorted(
        float(run_repository.get(run_id).state.attributes["tonnes_per_hour"])
        for run_id in rerun.run_ids
    )
    assert first_outcomes == second_outcomes
