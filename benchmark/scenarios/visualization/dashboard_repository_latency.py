"""Benchmark scenario: ``DashboardRepository.get()``/``list()`` latency
at representative dashboard-population scale (Visualization
implementation checklist, Benchmarks).

Standalone by design -- mirroring the established harness-free posture
of the other packages' scenarios. Results are recorded in
``benchmark/reports/visualization/``.

Scale rationale: a large enterprise accumulates saved dashboards per
user, per site, per role; 10³/10⁴/10⁵ spans "a team" through "a whole
enterprise, never pruned". ``get()`` is the hot open-a-dashboard path
and must stay O(1) (design spec §29).

Run: python benchmark/scenarios/visualization/dashboard_repository_latency.py
"""

from __future__ import annotations

import platform
import time

from mineproductivity.core import InMemoryRepository
from mineproductivity.visualization import Dashboard, by_owner

POPULATIONS = (1_000, 10_000, 100_000)
GET_REPEATS = 10_000
LIST_REPEATS = 5


def _dashboard(index: int) -> Dashboard:
    owner = "supervisor-a" if index % 2 == 0 else "supervisor-b"
    return Dashboard(id=f"DASH-{index:06d}", name=f"Board {index}", owner=owner)


def main() -> None:
    print("DashboardRepository.get()/list() latency (core.InMemoryRepository reference)")
    print(f"python={platform.python_version()} machine={platform.machine()}")
    print()
    print(f"{'boards':>8} {'get_us':>8} {'list_all_ms':>12} {'list_owner_ms':>14} {'matches':>8}")

    for population in POPULATIONS:
        repository: InMemoryRepository[Dashboard, str] = InMemoryRepository()
        for index in range(population):
            repository.add(_dashboard(index))

        middle_id = f"DASH-{population // 2:06d}"
        start = time.perf_counter()
        for _ in range(GET_REPEATS):
            repository.get(middle_id)
        get_seconds = (time.perf_counter() - start) / GET_REPEATS

        start = time.perf_counter()
        for _ in range(LIST_REPEATS):
            everything = repository.list()
        list_all_seconds = (time.perf_counter() - start) / LIST_REPEATS

        specification = by_owner("supervisor-a")
        start = time.perf_counter()
        for _ in range(LIST_REPEATS):
            matched = repository.list(specification)
        list_owner_seconds = (time.perf_counter() - start) / LIST_REPEATS

        assert len(everything) == population
        print(
            f"{population:>8} {get_seconds * 1e6:>8.2f} {list_all_seconds * 1e3:>12.2f}"
            f" {list_owner_seconds * 1e3:>14.2f} {len(matched):>8}"
        )


if __name__ == "__main__":
    main()
