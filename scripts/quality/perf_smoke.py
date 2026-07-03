"""Performance smoke test: not a benchmark suite -- a fast, CI-friendly
check that a handful of representative operations have not
*catastrophically* regressed (a stray O(n) become O(n^2), an accidental
per-call re-import, a broken cache). Thresholds are generous by design;
this is a tripwire for a real problem, not a performance tracker. Real
benchmarking is `benchmark/`'s job, once `mineproductivity.benchmark`
exists (see `benchmark/README.md`) -- this script does not depend on it.

Run locally or in CI:

    python scripts/quality/perf_smoke.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Wall-clock ceilings, deliberately generous for a loaded/shared CI
# runner. A failure here means something is wrong by an order of
# magnitude, not "10% slower than last week."
IMPORT_BUDGET_S = 5.0
REGISTRY_COMPUTE_BUDGET_S = 2.0
DEPENDENCY_GRAPH_BUDGET_S = 1.0


def _time_subprocess_import() -> float:
    """Cold-start import time, measured in a fresh interpreter so the
    result isn't skewed by whatever this script itself already
    imported."""
    start = time.perf_counter()
    subprocess.run(
        [sys.executable, "-c", "import mineproductivity.kpis"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    return time.perf_counter() - start


def _time_registry_batch_compute() -> tuple[float, int]:
    from mineproductivity.kpis import REGISTRY
    from mineproductivity.kpis.composite import CompositeKPI

    rows = [{"payload_t": 220.0 + i, "operating_h": 12.0} for i in range(500)]
    start = time.perf_counter()
    computed = 0
    for code in REGISTRY:
        kpi_cls = REGISTRY.get(code)
        if issubclass(kpi_cls, CompositeKPI):
            continue  # needs already-computed dependency results, not raw rows
        kpi_cls().compute(rows)
        computed += 1
    return time.perf_counter() - start, computed


def _time_dependency_graph_resolution() -> float:
    from mineproductivity.kpis import REGISTRY, DependencyGraph

    graph = DependencyGraph(REGISTRY)
    start = time.perf_counter()
    for code in REGISTRY:
        graph.topological_order(code)
    return time.perf_counter() - start


def main() -> int:
    failures: list[str] = []

    import_time = _time_subprocess_import()
    status = "OK" if import_time <= IMPORT_BUDGET_S else "FAIL"
    print(
        f"[{status}] cold import mineproductivity.kpis: {import_time:.3f}s (budget {IMPORT_BUDGET_S}s)"
    )
    if import_time > IMPORT_BUDGET_S:
        failures.append("import time")

    compute_time, n_kpis = _time_registry_batch_compute()
    status = "OK" if compute_time <= REGISTRY_COMPUTE_BUDGET_S else "FAIL"
    print(
        f"[{status}] compute {n_kpis} leaf KPIs x 500 rows: "
        f"{compute_time:.3f}s (budget {REGISTRY_COMPUTE_BUDGET_S}s)"
    )
    if compute_time > REGISTRY_COMPUTE_BUDGET_S:
        failures.append("registry batch compute time")

    graph_time = _time_dependency_graph_resolution()
    status = "OK" if graph_time <= DEPENDENCY_GRAPH_BUDGET_S else "FAIL"
    print(
        f"[{status}] resolve dependency order for every registered KPI: "
        f"{graph_time:.3f}s (budget {DEPENDENCY_GRAPH_BUDGET_S}s)"
    )
    if graph_time > DEPENDENCY_GRAPH_BUDGET_S:
        failures.append("dependency graph resolution time")

    if failures:
        print(f"\nPERFORMANCE SMOKE TEST FAILED: {', '.join(failures)}")
        return 1
    print("\nperformance smoke test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
