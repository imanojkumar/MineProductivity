"""Benchmark scenario: ``SimulationRunRepository.get()``/``list()``
latency at representative run-population scale (Simulation
implementation checklist, Benchmarks).

Standalone by design -- mirroring ``benchmark/scenarios/decision/``'s
and ``benchmark/scenarios/digital_twin/``'s established harness-free
posture. Results are recorded in ``benchmark/reports/simulation/``.

Scale rationale: a 500-trial Monte Carlo experiment per scenario per
shift accumulates ~10^4-10^5 runs per site per month if never pruned;
10^3/10^4/10^5 spans "one big experiment" through "a month of
experiments, never pruned." ``get()`` is the hot per-trial path and
must stay O(1) (design spec §36).

Run: python benchmark/scenarios/simulation/run_repository_latency.py
"""

from __future__ import annotations

import platform
import time
from datetime import datetime, timezone

from mineproductivity.core import InMemoryRepository
from mineproductivity.simulation import SimulationRun, SimulationState, by_scope

_EPOCH = datetime(2026, 7, 8, tzinfo=timezone.utc)

POPULATIONS = (1_000, 10_000, 100_000)
GET_REPEATS = 10_000
LIST_REPEATS = 5


def _run(index: int) -> SimulationRun:
    return SimulationRun(
        id=f"RUN-{index:06d}",
        scenario_code="FLEET.Surge" if index % 2 == 0 else "FLEET.Baseline",
        state=SimulationState(attributes={"outcome": float(index)}, simulated_time=_EPOCH),
    )


def main() -> None:
    print("SimulationRunRepository.get()/list() latency (core.InMemoryRepository reference)")
    print(f"python={platform.python_version()} machine={platform.machine()}")
    print()
    print(f"{'runs':>8} {'get_us':>8} {'list_all_ms':>12} {'list_scope_ms':>14} {'matches':>8}")

    for population in POPULATIONS:
        repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        for index in range(population):
            repository.add(_run(index))

        middle_id = f"RUN-{population // 2:06d}"
        start = time.perf_counter()
        for _ in range(GET_REPEATS):
            repository.get(middle_id)
        get_seconds = (time.perf_counter() - start) / GET_REPEATS

        start = time.perf_counter()
        for _ in range(LIST_REPEATS):
            everything = repository.list()
        list_all_seconds = (time.perf_counter() - start) / LIST_REPEATS

        specification = by_scope({"scenario_code": "FLEET.Surge"})
        start = time.perf_counter()
        for _ in range(LIST_REPEATS):
            matched = repository.list(specification)
        list_scope_seconds = (time.perf_counter() - start) / LIST_REPEATS

        assert len(everything) == population
        print(
            f"{population:>8} {get_seconds * 1e6:>8.2f} {list_all_seconds * 1e3:>12.2f}"
            f" {list_scope_seconds * 1e3:>14.2f} {len(matched):>8}"
        )


if __name__ == "__main__":
    main()
