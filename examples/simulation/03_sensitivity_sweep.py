"""``SensitivityAnalyzer.sweep()`` over a single ``Scenario``
parameter, with distributional treatment of the outcomes handed to
``analytics`` (spec 09 sec. 20) -- one run per swept value, ordered to
match the values, so results zip back together trivially.

Run: python examples/simulation/03_sensitivity_sweep.py
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
    SensitivityAnalyzer,
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
class CrusherFeedModel(MonteCarloModel):
    """Projects crusher feed rate from the swept truck count
    (example-local model; seed-deterministic)."""

    meta = SimulationMetadata(
        code="MONTECARLO.CrusherFeed",
        category=SimulationCategory.MONTE_CARLO,
        description="Projects crusher feed rate from the swept truck count.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        trucks = int(scenario.parameters["trucks"])
        rng = random.Random(random_seed)
        feed = min(trucks * 175.0, 5000.0) * rng.uniform(0.95, 1.02)  # crusher-capped
        return SimulationResult(
            final_state=SimulationState(
                attributes={"feed_tph": feed},
                simulated_time=NOW + scenario.time_horizon,
            )
        )


def main() -> None:
    print("--- 1. A base scenario and the parameter to sweep ---")
    base = Scenario(
        code="PLANT.CrusherFeedStudy",
        model_code="MONTECARLO.CrusherFeed",
        parameters={"trucks": 20},
        time_horizon=timedelta(hours=12),
    )
    values = [20, 24, 28, 32, 36]
    print(f"base={base.code!r}, sweeping trucks over {values}")

    print()
    print("--- 2. One run per swept value, ordered to match ---")
    repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    runner = ExperimentRunner(
        executor=SimulationExecutor(
            repository=repository,
            clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED),
        ),
        repository=repository,
    )
    analyzer = SensitivityAnalyzer(runner=runner)
    context = SimulationContext(event_store=_InMemoryEventStore())
    experiment = analyzer.sweep(base, parameter="trucks", values=values, context=context)

    outcomes: list[float] = []
    for trucks, run_id in zip(values, experiment.run_ids, strict=True):
        feed = float(repository.get(run_id).state.attributes["feed_tph"])
        outcomes.append(feed)
        print(f"trucks={trucks:>2} -> feed={feed:7.1f} t/h")
    print("(the crusher cap flattens the curve past ~28 trucks)")

    print()
    print("--- 3. Distributional treatment is analytics' job, not simulation's ---")
    shape, interval = analyzer.summarize(outcomes, confidence=0.95)
    print(f"skewness={shape.skewness:+.3f} kurtosis={shape.kurtosis:.3f}")
    print(
        f"{interval.confidence:.0%} CI around the sweep mean:"
        f" [{interval.lower:.1f}, {interval.upper:.1f}] t/h ({interval.method})"
    )

    print()
    print("--- 4. The base scenario is untouched -- variants were transient copies ---")
    print(f"base parameters still: {dict(base.parameters)}")


if __name__ == "__main__":
    main()
