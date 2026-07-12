"""The design spec 09 sec. 17 worked example, end-to-end: a 500-trial
Monte Carlo experiment seeded from a real ``digital_twin.TwinSnapshot``,
with trial outcomes summarized through ``analytics`` via
``ScenarioComparator`` -- ``simulation`` orchestrates; it never
recomputes a twin's state or re-derives a statistic.

The concrete model below is example-local: the package itself ships
zero concrete simulation models by design (interface-only
methodologies, spec 09 sec. 13-16).

Run: python examples/simulation/01_monte_carlo_experiment.py
"""

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

NOW = datetime(2026, 7, 8, 6, 0, tzinfo=timezone.utc)


@register
class HaulCycleVariabilityModel(MonteCarloModel):
    """Perturbs the snapshot-seeded fleet throughput per trial -- all
    randomness derives from the supplied random_seed, so every trial is
    reproducible and safely concurrent (spec 09 sec. 33)."""

    meta = SimulationMetadata(
        code="MONTECARLO.HaulCycleVariability",
        category=SimulationCategory.MONTE_CARLO,
        description=(
            "Perturbs the snapshot-seeded fleet throughput per trial -- all "
            "randomness derives from the supplied random_seed."
        ),
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
                simulated_time=NOW + scenario.time_horizon,
            )
        )


def main() -> None:
    print("--- 1. Start from a real twin snapshot, not a hand-authored guess ---")
    snapshot = TwinSnapshot(
        twin_id="FLEET-NORTH",
        state=TwinState(attributes={"tonnes_per_hour": 4200.0}, captured_at=NOW),
        status=TwinStatus.SYNCHRONIZED,
        as_of=AsOf(utc=NOW),
    )
    print(f"snapshot of {snapshot.twin_id}: {dict(snapshot.state.attributes)}")

    print()
    print("--- 2. A governed Scenario names the model, parameters, and horizon ---")
    scenario = Scenario(
        code="FLEET.NightShiftSurge",
        model_code="MONTECARLO.HaulCycleVariability",
        parameters={"trucks_added": 3},
        time_horizon=timedelta(hours=12),
        initial_state=snapshot,
    )
    print(f"scenario={scenario.code!r} v{scenario.version} parameters={dict(scenario.parameters)}")

    print()
    print("--- 3. 500 independent, concurrently-dispatched, seeded trials ---")
    run_repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    executor = SimulationExecutor(
        repository=run_repository,
        clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED),
    )
    runner = ExperimentRunner(executor=executor, repository=run_repository)
    context = SimulationContext(event_store=_InMemoryEventStore())
    experiment = runner.run_trials(scenario, trials=500, context=context)
    print(f"experiment {experiment.name!r}: {len(experiment.run_ids)} runs completed")

    print()
    print("--- 4. Summarize through analytics -- simulation owns no statistics ---")
    results = [run_repository.get(run_id) for run_id in experiment.run_ids]
    summary = ScenarioComparator().compare({"night_shift_surge": [run.state for run in results]})
    surge = summary["night_shift_surge"]
    print(f"n={surge.n} mean={surge.mean:.1f} t/h")
    print(f"p50={surge.percentiles[50]:.1f} p90={surge.percentiles[90]:.1f}")
    print(f"range=[{surge.minimum:.1f}, {surge.maximum:.1f}]")


if __name__ == "__main__":
    main()
