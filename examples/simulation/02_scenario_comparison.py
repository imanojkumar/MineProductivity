"""``ScenarioComparator`` composed over two named scenarios' trial
outcomes -- the comparison judgment itself (which outcome is "better")
stays with the caller; ``simulation`` assembles the series and
``analytics`` computes the statistics (spec 09 sec. 19).

Run: python examples/simulation/02_scenario_comparison.py
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from mineproductivity.core import InMemoryRepository
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
class ShiftThroughputModel(MonteCarloModel):
    """Projects a shift's throughput from the scenario's truck count --
    seed-deterministic per trial (example-local model)."""

    meta = SimulationMetadata(
        code="MONTECARLO.ShiftThroughput",
        category=SimulationCategory.MONTE_CARLO,
        description=(
            "Projects a shift's throughput from the scenario's truck count -- "
            "seed-deterministic per trial."
        ),
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        trucks = int(scenario.parameters["trucks"])
        rng = random.Random(random_seed)
        throughput = trucks * 180.0 * rng.uniform(0.85, 1.05)
        return SimulationResult(
            final_state=SimulationState(
                attributes={"tonnes_per_hour": throughput},
                simulated_time=NOW + scenario.time_horizon,
            )
        )


def main() -> None:
    print("--- 1. Two governed scenarios differing in one assumption ---")
    baseline = Scenario(
        code="FLEET.BaselineShift",
        model_code="MONTECARLO.ShiftThroughput",
        parameters={"trucks": 24},
        time_horizon=timedelta(hours=12),
    )
    surge = Scenario(
        code="FLEET.SurgeShift",
        model_code="MONTECARLO.ShiftThroughput",
        parameters={"trucks": 27},
        time_horizon=timedelta(hours=12),
    )
    print(f"{baseline.code}: trucks={baseline.parameters['trucks']}")
    print(f"{surge.code}:    trucks={surge.parameters['trucks']}")

    print()
    print("--- 2. 200 trials per scenario ---")
    repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    runner = ExperimentRunner(
        executor=SimulationExecutor(
            repository=repository,
            clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED),
        ),
        repository=repository,
    )
    context = SimulationContext(event_store=_InMemoryEventStore())
    experiments = {
        "baseline": runner.run_trials(baseline, trials=200, context=context),
        "surge": runner.run_trials(surge, trials=200, context=context),
    }

    print()
    print("--- 3. One analytics-backed summary per scenario ---")
    summaries = ScenarioComparator().compare(
        {
            key: [repository.get(run_id).state for run_id in experiment.run_ids]
            for key, experiment in experiments.items()
        }
    )
    for key, summary in summaries.items():
        print(
            f"{key:>8}: mean={summary.mean:7.1f} t/h  "
            f"p90={summary.percentiles[90]:7.1f}  n={summary.n}"
        )

    print()
    print("--- 4. The judgment stays with the caller (a decision-layer question) ---")
    uplift = summaries["surge"].mean - summaries["baseline"].mean
    print(f"observed mean uplift from 3 extra trucks: {uplift:+.1f} t/h")


if __name__ == "__main__":
    main()
