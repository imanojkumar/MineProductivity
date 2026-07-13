# Examples — mineproductivity.optimization

## Purpose

Runnable, minimal, self-contained scripts demonstrating the Optimization package: a mixed-integer fleet allocation seeded from a `digital_twin.TwinSnapshot`, plan comparison, a sensitivity sweep, a candidate-scenario search composed over `simulation`, and a third-party solver-adapter plugin. Every concrete solver model in these scripts is example-local — the package itself ships zero concrete solver models by design (interface-only paradigms, design spec §11–§16, ADR-0010).

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/optimization/` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the Optimization public API.
- Serve as executable documentation that stays correct because it is actually run.
- Demonstrate the §3.2 discipline end-to-end: problems seed from `digital_twin.TwinSnapshot`s, candidate search composes `simulation.ExperimentRunner`, and every statistical judgment is `analytics`' — `optimization` orchestrates and never re-derives a solver library's arithmetic or a statistic.

## Contents

- `01_mip_fleet_allocation.py` — a mixed-integer fleet/shift allocation problem seeded from a real `TwinSnapshot`, solved end-to-end through `OptimizationExecutor` with a hand-computable optimum.
- `02_plan_comparison.py` — two candidate plans, each solved across five ore-grade scenarios, one analytics-backed `StatisticalSummary` per plan via `PlanComparator`; the "which is better" judgment stays with the caller.
- `03_sensitivity_sweep.py` — `SensitivityAnalyzer.sweep()` over a single constraint bound (one re-solve per value, ordered to match), with `distribution`/`confidence_interval` delegation for the outcome treatment; proves the base problem is never edited in place.
- `04_candidate_scenario_search.py` — a search over candidate fleet sizes scored by `simulation.ExperimentRunner`, the per-candidate score distributions compared with `PlanComparator` (design spec §17); `optimization` never constructs a `simulation.SimulationRun` itself.
- `05_plugin_solver_adapter.py` — a third-party-style category-ABC subclass registered via entry points (`EntryPointSpec(group="mineproductivity.optimization", target_registry="optimization")`, design spec §31), mirroring `examples/registry/01_register_and_discover.py`'s real-discovery pattern — the only place a real solver library would be imported.

## Dependencies

`mineproductivity[analytics]` (for `analytics`' statistical primitives, used by `PlanComparator`/`SensitivityAnalyzer`). No network access; every snapshot and scenario is constructed in-script.

## Running the Examples

```bash
pip install -e ".[analytics]"
python examples/optimization/01_mip_fleet_allocation.py
python examples/optimization/02_plan_comparison.py
python examples/optimization/03_sensitivity_sweep.py
python examples/optimization/04_candidate_scenario_search.py
python examples/optimization/05_plugin_solver_adapter.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add a linear-programming and a network-optimization walkthrough once first-party or third-party solver adapters implementing those interface-only extension points exist (deliberately never shipped inside `optimization` itself, design spec §11–§16).

## References

- [`docs/architecture/10_Optimization_Design_Specification.md`](../../docs/architecture/10_Optimization_Design_Specification.md) §9, §11–§16, §17, §19–§20, §31
- [`src/mineproductivity/optimization/README.md`](../../src/mineproductivity/optimization/README.md)
- [`docs/adr/ADR-0010-Optimization.md`](../../docs/adr/ADR-0010-Optimization.md)
