# mineproductivity.optimization

## Purpose

Prescriptive plan search over governed problem statements — an orchestration layer over six pluggable, interface-only solving paradigms (LP, MIP, CP, multi-objective, evolutionary/metaheuristic, network), never importing a solver library itself (design spec §17's adapter pattern).

## Scope

**What belongs here:** problem definition/governance, run execution/orchestration, the six category ABCs, plan comparison and post-optimality sensitivity (statistics delegated to `analytics`).

**What must never belong here:** a concrete solver or algorithm (adapter plugins own that, §17); KPI/statistical/decision/twin/simulation computation (§3.2); a caching module (§26's documented non-need).

## Responsibilities

- Implements the `optimization` subsystem per the Reference Implementation Blueprint v1.0 — the complete design spec §6 module list (twenty modules). `OptimizationProblem` (§9) is the governed artifact (publish/supersede via `ProblemConflictError`; `Constraint.expression` is a solver-independent string this package never parses). `OptimizationRun`/`OptimizationExecutor` (§10) follow the established run-entity/executor pattern: category-driven dispatch (`_solve_lp`/`_solve_mip`/`_solve_cp`/`_solve_pareto`/`_iterate`/`_solve_network`), §11/§14 pairing rules enforced before dispatch, iterative categories looped to convergence or `parameters["max_iterations"]`, infeasibility expressed as `OptimizationResult(feasible=False)` — never a raise (§28). `PlanComparator`/`SensitivityAnalyzer` (§19–§20) delegate every statistic to `analytics`; a candidate-scenario search composes `simulation.ExperimentRunner` (§17). `OptimizationRunRepository` (§24) is a literal `type` alias over `core.BaseRepository[OptimizationRun, str]`.

## Contents

`abstractions.py`, `metadata.py`, `problem.py`, `run.py`, `state.py`, the six category modules (`linear_programming.py`, `mixed_integer_programming.py`, `constraint_programming.py`, `multi_objective.py`, `evolutionary.py`, `network_optimization.py` — all interface-only, zero concrete subclasses), `executor.py`, `comparison.py`, `sensitivity.py`, `discovery.py`, `persistence.py`, `result.py`, `_registry.py`, `exceptions.py`, `__init__.py` (36 public symbols, the full design spec §7 list), `README.md`.

## Dependencies

**Depends on:** `core`, `events`, `registry`, `kpis`, `analytics`, `decision`, `digital_twin`, `simulation` (exercised); `ontology`/`plugins`/`connectors` permitted but unexercised. Never imports OR-Tools, Pyomo, PuLP, or SciPy.

**Depended on by:** `agents`, `visualization`

## Future Work

First concrete solver adapters per category (plugins, §17/§30); production-grade `OptimizationRunRepository` backend; whatever `agents`/`visualization` need as they move to implemented.

## References

- [`docs/architecture/10_Optimization_Design_Specification.md`](../../../docs/architecture/10_Optimization_Design_Specification.md)
- [`docs/adr/ADR-0010-Optimization.md`](../../../docs/adr/ADR-0010-Optimization.md)
