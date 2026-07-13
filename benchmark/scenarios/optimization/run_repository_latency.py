"""Benchmark scenario: ``OptimizationRunRepository.get()``/``list()``
latency at representative run-population scale (Optimization
implementation checklist, Benchmarks).

Standalone by design -- mirroring ``benchmark/scenarios/simulation/``'s
established harness-free posture. Results are recorded in
``benchmark/reports/optimization/``.

Scale rationale: a post-optimality sweep or a candidate-scenario search
accumulates one run per swept value per re-solve; 10³/10⁴/10⁵ spans
"one big sweep" through "a month of sweeps, never pruned". ``get()`` is
the hot per-re-solve path and must stay O(1) (design spec §36).

Run: python benchmark/scenarios/optimization/run_repository_latency.py
"""

from __future__ import annotations

import platform
import time

from mineproductivity.core import InMemoryRepository
from mineproductivity.optimization import OptimizationRun, OptimizationState, by_scope

POPULATIONS = (1_000, 10_000, 100_000)
GET_REPEATS = 10_000
LIST_REPEATS = 5


def _run(index: int) -> OptimizationRun:
    return OptimizationRun(
        id=f"RUN-{index:06d}",
        problem_code="FLEET.Surge" if index % 2 == 0 else "FLEET.Baseline",
        state=OptimizationState(attributes={"outcome": float(index)}),
    )


def main() -> None:
    print("OptimizationRunRepository.get()/list() latency (core.InMemoryRepository reference)")
    print(f"python={platform.python_version()} machine={platform.machine()}")
    print()
    print(f"{'runs':>8} {'get_us':>8} {'list_all_ms':>12} {'list_scope_ms':>14} {'matches':>8}")

    for population in POPULATIONS:
        repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
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

        specification = by_scope({"problem_code": "FLEET.Surge"})
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
