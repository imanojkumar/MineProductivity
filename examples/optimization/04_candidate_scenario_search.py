"""A candidate-scenario search (design spec §17): each candidate fleet
size is scored by a ``simulation.ExperimentRunner`` Monte Carlo
experiment, and the per-candidate score distributions are compared with
``optimization.PlanComparator``. ``optimization`` composes
``simulation`` directly and never constructs a ``simulation.SimulationRun``
itself -- it hands scenarios to the runner and reads the outcomes back.

Both concrete models are example-local.

Run: python examples/optimization/04_candidate_scenario_search.py
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from mineproductivity.core import InMemoryRepository
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.optimization import (
    OptimizationResult,
    PlanComparator,
)
from mineproductivity.simulation import (
    ExperimentRunner,
    MonteCarloModel,
    Scenario,
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
CANDIDATES = (24, 27, 30)
TRIALS = 8


@register
class FleetScoreModel(MonteCarloModel):
    """Scores a candidate fleet size per trial with seed-deterministic
    haul-cycle variability -- example-local, safely concurrent."""

    meta = SimulationMetadata(
        code="MONTECARLO.FleetCandidateScore",
        category=SimulationCategory.MONTE_CARLO,
        description="Scores a candidate fleet size per trial (seed-deterministic).",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        trucks = int(scenario.parameters["trucks"])
        score = trucks * 180.0 * random.Random(random_seed).uniform(0.90, 1.10)
        return SimulationResult(
            final_state=SimulationState(
                attributes={"score": score},
                simulated_time=NOW + scenario.time_horizon,
            )
        )


def main() -> None:
    print("--- 1. A simulation runner scores each candidate fleet size ---")
    sim_repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    runner = ExperimentRunner(
        executor=SimulationExecutor(
            repository=sim_repository,
            clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED),
        ),
        repository=sim_repository,
    )
    context = SimulationContext(event_store=_InMemoryEventStore())

    results_by_candidate: dict[str, list[OptimizationResult]] = {}
    for trucks in CANDIDATES:
        scenario = Scenario(
            code=f"CANDIDATE.Trucks{trucks}",
            model_code="MONTECARLO.FleetCandidateScore",
            parameters={"trucks": trucks},
            time_horizon=timedelta(hours=12),
        )
        experiment = runner.run_trials(scenario, trials=TRIALS, context=context)
        # Wrap each trial's score as an OptimizationResult -- the bridge
        # from a simulation outcome to an optimization-comparable plan.
        results_by_candidate[f"trucks_{trucks}"] = [
            OptimizationResult(
                objective_value=float(sim_repository.get(run_id).state.attributes["score"]),
                solution={"trucks": float(trucks)},
            )
            for run_id in experiment.run_ids
        ]
        print(f"candidate trucks={trucks}: {len(experiment.run_ids)} trials scored")

    print()
    print("--- 2. Compare the candidates' score distributions via analytics ---")
    summaries = PlanComparator().compare(results_by_candidate)
    for candidate, summary in summaries.items():
        print(
            f"{candidate:>10}: n={summary.n} mean={summary.mean:7.1f} "
            f"p50={summary.percentiles[50]:7.1f} "
            f"range=[{summary.minimum:7.1f}, {summary.maximum:7.1f}]"
        )

    print()
    print("--- 3. optimization never built a SimulationRun; it read the outcomes ---")
    print("(the winning candidate is the caller's call, informed by these summaries)")


if __name__ == "__main__":
    main()
