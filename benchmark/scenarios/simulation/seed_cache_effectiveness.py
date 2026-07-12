"""Benchmark scenario: ``SimulationStateCache`` hit-rate and time saved
across a representative Monte Carlo experiment's repeated trials
(Simulation implementation checklist, Benchmarks).

Standalone by design -- mirroring the sibling benchmark directories'
harness-free posture. Results are recorded in
``benchmark/reports/simulation/``.

Method: a scenario anchored to a historical ``AsOf`` over a
10,000-event history is trialed 200 times. Uncached, every trial pays
a full ``EventStore.replay()`` (design spec §26's motivating waste);
cached, the first trial seeds and the remaining 199 hit the
``(scenario_code, as_of)`` key. Both passes execute the identical
model; the delta is the cache's contribution alone.

Run: python benchmark/scenarios/simulation/seed_cache_effectiveness.py
"""

from __future__ import annotations

import platform
import time
from datetime import datetime, timedelta, timezone

from mineproductivity.core import InMemoryRepository
from mineproductivity.events import AsOf, CycleEvent
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.identifier import EventID
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.events.versioning import EventVersion
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
    SimulationStateCache,
    TimeProgressionMode,
    register,
)

_GENESIS = datetime(2026, 1, 1, tzinfo=timezone.utc)

HISTORY_LENGTH = 10_000
TRIALS = 200


@register
class _SeedReaderModel(MonteCarloModel):
    """Reads the replay-seeded census and echoes it -- the trial cost
    itself is negligible, isolating the seeding cost."""

    meta = SimulationMetadata(
        code="MONTECARLO.CacheBenchSeedReader",
        category=SimulationCategory.MONTE_CARLO,
        description="Echoes the replay-seeded census; negligible trial cost.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        return SimulationResult()


def _envelope(index: int) -> EventEnvelope[CycleEvent]:
    moment = _GENESIS + timedelta(seconds=index)
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=CycleEvent(
            equipment_id="EQ-1",
            shift_id="A",
            queue_min=1.0,
            spot_min=0.5,
            load_min=2.0,
            haul_min=8.0,
            dump_min=1.0,
            return_min=6.0,
            payload_t=220.0,
        ),
        event_time_utc=moment,
        processing_time_utc=moment,
        ingestion_time_utc=moment,
        metadata=EventMetadata(name="cycle", source_system="bench"),
    )


def _timed_experiment(*, cached: bool, store: _InMemoryEventStore) -> float:
    repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    cache = SimulationStateCache() if cached else None
    executor = SimulationExecutor(
        repository=repository,
        clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED),
        cache=cache,
    )
    runner = ExperimentRunner(executor=executor, repository=repository)
    scenario = Scenario(
        code=f"BENCH.CacheStudy.{'cached' if cached else 'uncached'}",
        model_code="MONTECARLO.CacheBenchSeedReader",
        time_horizon=timedelta(hours=1),
        as_of=AsOf(utc=_GENESIS + timedelta(seconds=HISTORY_LENGTH + 1)),
    )
    context = SimulationContext(event_store=store)
    start = time.perf_counter()
    experiment = runner.run_trials(scenario, trials=TRIALS, context=context)
    elapsed = time.perf_counter() - start
    assert len(experiment.run_ids) == TRIALS
    return elapsed


def main() -> None:
    print("SimulationStateCache effectiveness across repeated Monte Carlo trials")
    print(f"python={platform.python_version()} machine={platform.machine()}")
    print(f"history={HISTORY_LENGTH} events, trials={TRIALS}")
    print()

    store = _InMemoryEventStore()
    for index in range(HISTORY_LENGTH):
        assert store.append(_envelope(index)).is_ok

    uncached = _timed_experiment(cached=False, store=store)
    cached = _timed_experiment(cached=True, store=store)
    replays_saved = TRIALS - 1
    print(f"{'mode':>10} {'total_s':>9} {'per_trial_ms':>13}")
    print(f"{'uncached':>10} {uncached:>9.2f} {uncached / TRIALS * 1e3:>13.2f}")
    print(f"{'cached':>10} {cached:>9.2f} {cached / TRIALS * 1e3:>13.2f}")
    print()
    print(
        f"hit-rate: {replays_saved}/{TRIALS} trials served from cache "
        f"({replays_saved / TRIALS:.1%}); time saved: {uncached - cached:.2f}s "
        f"({(1 - cached / uncached):.1%})"
    )


if __name__ == "__main__":
    main()
