# Optimization — Implementation Checklist

**Package:** `mineproductivity.optimization`
**Governing specification:** [`docs/architecture/10_Optimization_Design_Specification.md`](../architecture/10_Optimization_Design_Specification.md)
**Architecture Decision Record:** [`docs/adr/ADR-0010-Optimization.md`](../adr/ADR-0010-Optimization.md)
**Status:** Implemented and released (software v1.9.0, 2026-07-12).

All items below are satisfied: the complete design spec §6 module list is implemented, the unit suite passes with ≥95% coverage (99% including branches), the five `examples/optimization/` scripts and both `benchmark/reports/optimization/` reports exist and are `mypy --strict`/`ruff`-clean, and the six §35 acceptance proofs each run as dedicated tests. No architectural changes were made relative to the locked v1.2.0 design.

Binding, **locked** implementation contract for `optimization` — the fifth package built on top of the Foundation Layer, sitting directly above the now-locked `simulation`. Nothing described here may be implemented before this checklist and its governing specification exist in reviewed form, and nothing may be implemented that is not represented by an item on this list. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [x] Design specification (`10_Optimization_Design_Specification.md`) read in full by the implementer, including every cross-reference to specs 01–09.
- [x] ADR-0010 read in full; the rationale for `optimization` existing as a separate package above `simulation` (and for the interface-only treatment of all six solving paradigms) is understood, not merely accepted.
- [x] `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, `kpis`, `analytics`, `decision`, `digital_twin`, `simulation` available and importable, exactly as released; no lower package file is modified as a side effect of this work.
- [x] Confirmed: `optimization` will not import `agents` or `visualization` under any circumstance — neither package exists yet (design spec §5, §37).
- [x] Confirmed: no lower package (`core` through `simulation`) will be modified to import or otherwise reference `optimization` (design spec §5).

## Package Structure

- [x] `src/mineproductivity/optimization/` created matching design spec §6 exactly: `abstractions.py`, `metadata.py`, `problem.py`, `run.py`, `state.py`, `linear_programming.py`, `mixed_integer_programming.py`, `constraint_programming.py`, `multi_objective.py`, `evolutionary.py`, `network_optimization.py`, `executor.py`, `comparison.py`, `sensitivity.py`, `discovery.py`, `persistence.py`, `result.py`, `_registry.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [x] `optimization/README.md` written following the `core/README.md` template.
- [x] Confirmed `linear_programming.py`, `mixed_integer_programming.py`, `constraint_programming.py`, `multi_objective.py`, `evolutionary.py`, and `network_optimization.py` each contain zero concrete, non-test subclasses of their respective category ABC (mechanical grep/AST check — design spec §11–§16, §35's interface-purity proof).
- [x] Confirmed no module under `src/mineproductivity/optimization/` performs direct KPI, statistical, decision, twin-state, or simulation-projection computation of its own — every such value arrives via the corresponding lower package's public API (design spec §3.2, §35's no-fact-recomputation proof).
- [x] Confirmed `comparison.py`/`sensitivity.py` contain zero direct mean/percentile/correlation arithmetic — every such computation is a call into `analytics` (design spec §35's no-statistics-reimplementation proof).
- [x] Confirmed no module under `src/mineproductivity/optimization/` imports, or contains a string reference to, `ortools`, `pyomo`, `pulp`, or `scipy` (design spec §17, §35's no-solver-coupling proof).

## Public API

- [x] `optimization/__init__.py` exports exactly the symbol list in design spec §7, alphabetized `__all__`.
- [x] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py` and every existing package's own copy of it.
- [x] `TestNoForbiddenDependencies` AST-walks every `optimization` submodule for a forbidden import (`agents`, `visualization`) — mirrors every existing package's own copy of this test (design spec §5).
- [x] A second, reverse-direction test asserts no file under `src/mineproductivity/{core,ontology,events,registry,plugins,connectors,kpis,analytics,decision,digital_twin,simulation}/` imports `mineproductivity.optimization` (design spec §5) — the `simulation`-package precedent for this test extended one layer up.

## Optimization Abstractions (§8)

- [x] `OptimizationModel` (§8) — `meta: ClassVar[OptimizationMetadata]`; deliberately no shared abstract solve method.
- [x] `OptimizationContext` (§8) — `kpi_results`, `analytics_results`, `decision_results`, `twin_snapshot`, `simulation_results`, each defaulting to an empty sequence or `None`.
- [x] Confirmed `OptimizationModel` subclasses (of every category) are stateless — no instance attribute is mutated by any category method (§29, §32).

## Problem Definition (§9)

- [x] `ObjectiveDirection`, `ConstraintOperator`, `VariableDomain` enums (§9) implemented exactly as specified.
- [x] `Objective`, `Constraint`, `DecisionVariable` (§9) — frozen `core.BaseValueObject`s, fields exactly as specified.
- [x] `ProblemStatus` enum (§9) — exactly `Proposed`/`Active`/`Superseded`/`Retired`.
- [x] `OptimizationProblem` (§9) — frozen `core.BaseValueObject`; `code`, `version` (default `"1.0.0"`), `status`, `model_code`, `objectives`, `constraints`, `variables`, `parameters`, `initial_state` (`TwinSnapshot | None`), `as_of` (`AsOf | None`); `validate()` rejects an empty `code`/`model_code`, empty `objectives`/`variables`.
- [x] Confirmed an `Active` `OptimizationProblem` is never edited in place anywhere in the codebase — a changed problem is published as a new version, with the prior version transitioned to `Superseded` (§9, §25, §34's recorded anti-pattern).
- [x] `ProblemConflictError` raised for a materially-different re-registration under an existing, `Active` problem code without a version bump (§9, §25).
- [x] Confirmed no dependency-graph-shaped mechanism exists for `OptimizationProblem`'s constraints/variables (§9's documented non-need).

## Optimization Execution (§10)

- [x] `RunStatus` enum (§10) — exactly `Scheduled`/`Running`/`Paused`/`Completed`/`Failed`.
- [x] `OptimizationRun` (§10) — subclasses `core.BaseEntity[str]` directly; `problem_code`, `state: OptimizationState`, `status: RunStatus`; `with_state()` non-overridden, produces a new instance via `dataclasses.replace`, never mutates `self`.
- [x] Identity/equality proven: `OptimizationRun.__eq__`/`__hash__` inherited unchanged from `BaseEntity` (identity-based on `id`, ignoring `state`/`status`); no override anywhere in the package.
- [x] Lifecycle transitions proven to match design spec §10's state diagram exactly; `Completed` and `Failed` proven terminal (no transition out of either).
- [x] `OptimizationExecutor` (§6, §10) — dispatches to the registered `OptimizationModel`'s category-specific method based on the `OptimizationProblem.model_code`'s registered `OptimizationCategory`, never by branching on the model's concrete Python type; loops iterative categories to convergence or a termination bound; persists the resulting state via a `remove`-then-`add` pair against `OptimizationRunRepository`.
- [x] `OptimizationExecutor`'s dispatch and persistence sequence tested against design spec §10's sequence diagram exactly, including both the single-shot and iterative-category branches.
- [x] Confirmed a legitimately infeasible problem returns an `OptimizationResult(feasible=False, ...)` with a warning, never a raised exception.

## Linear Programming, Mixed Integer Programming, Constraint Programming, Multi-Objective, Evolutionary/Metaheuristic, Network Optimization Interfaces (§11–§16)

- [x] `LinearProgrammingModel` (§11) — `_solve_lp(problem, *, context) -> OptimizationResult` abstract; zero concrete subclasses shipped.
- [x] `MixedIntegerProgrammingModel` (§12) — `_solve_mip(problem, *, context) -> OptimizationResult` abstract; zero concrete subclasses shipped.
- [x] `ConstraintProgrammingModel` (§13) — `_solve_cp(problem, *, context) -> OptimizationResult` abstract; zero concrete subclasses shipped.
- [x] `MultiObjectiveModel` (§14) — `_solve_pareto(problem, *, context) -> ParetoResult` abstract; zero concrete subclasses shipped.
- [x] `EvolutionaryMetaheuristicModel` (§15) — `_iterate(problem, state, *, context) -> OptimizationState` abstract; zero concrete subclasses shipped.
- [x] `NetworkOptimizationModel` (§16) — `_solve_network(problem, *, context) -> OptimizationResult` abstract; zero concrete subclasses shipped.
- [x] Confirmed a `Problem` mixing non-continuous `DecisionVariable`s with an LP-category `model_code` is a validation error (§11, §27).
- [x] Confirmed no concrete `EvolutionaryMetaheuristicModel` implementation anywhere in the test suite holds mutable random-number-generator state across `_iterate` calls — every iteration's randomness derives solely from a seed in `problem.parameters`/`state.attributes` (§33, §34's recorded anti-pattern).
- [x] Confirmed goal programming is documented and tested as an `OptimizationProblem`-authoring pattern against `MixedIntegerProgrammingModel`/`LinearProgrammingModel`, not a separate category or ABC (§12).
- [x] Confirmed a network-optimization problem's graph structure is carried in `OptimizationProblem.parameters`, with no first-class `Node`/`Edge` value object introduced (§16).

## Solver Adapter Pattern (§17)

- [x] Confirmed no module under `src/mineproductivity/optimization/` imports OR-Tools, Pyomo, PuLP, or SciPy (§17, §35's no-solver-coupling proof).
- [x] A scripted integration test exercises a fixture "adapter" plugin (registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern) that subclasses one category ABC, proving the platform-side dispatch and registration path works end to end without this package depending on the fixture's own translation logic.
- [x] A scripted candidate-scenario search built on `simulation.ExperimentRunner.run_trials` (§17) is proven to produce the expected `simulation.Experiment`, without this package ever constructing a `simulation.SimulationRun` directly.

## Optimization Outputs, Plan Comparison, Sensitivity Analysis (§18, §19, §20)

- [x] `OptimizationResult` (§18) — frozen `core.BaseValueObject`; `run_id`, `computed_at`, `warnings`, `feasible` (default `True`), `objective_value`, `solution`.
- [x] `ParetoResult` (§18) — subclasses `OptimizationResult`; adds `front: tuple[OptimizationResult, ...]`.
- [x] Confirmed `OptimizationState` is **not** an `OptimizationResult` subclass (it represents the run's condition itself, not the outcome of an orchestration call about it).
- [x] `PlanComparator.compare()` (§19) implemented; confirmed every comparison delegates to `analytics.describe()`/`StatisticalSummary` — no mean/percentile computation exists in this package's own code.
- [x] `SensitivityAnalyzer.sweep()` (§20) implemented; confirmed every sweep re-solves via `OptimizationExecutor` and hands its `OptimizationResult`s to `analytics`' `DistributionSummary`/`confidence_interval` — no correlation/regression computation exists in this package's own code.
- [x] Delegation tests assert the actual `analytics` primitive invoked by `PlanComparator`/`SensitivityAnalyzer` (e.g. `describe`), never re-derive the expected statistic independently inside the test (§35).

## Optimization Registry and Discovery (§21, §22)

- [x] `optimization._registry.REGISTRY`/`register` (§21) — `Registry[str, type[OptimizationModel]]`, raising `OptimizationValidationError` for an empty code and `OptimizationVersionConflictError` for a materially-different re-registration under an existing code.
- [x] `EntryPointSpec(group="mineproductivity.optimization", target_registry="optimization")` discovery wired via `registry.EntryPointDiscovery` (§31).
- [x] `by_category()`/`by_scope()` (§22) — plain `core.PredicateSpecification` factories; composed with `OptimizationRunRepository.list()`; confirmed to return an empty sequence (never raise) for a filter matching nothing.
- [x] Confirmed the three-way distinction (`REGISTRY` = which model types are known; `OptimizationRunRepository` = which run instances currently exist; `discovery.py` = query facade over the instance store) is never conflated anywhere in the codebase (§21).

## Serialization and Persistence (§23, §24)

- [x] Every `OptimizationState`/`Objective`/`Constraint`/`DecisionVariable`/`OptimizationProblem`/`OptimizationResult` subclass and `OptimizationRun` itself confirmed to serialize via `core.serialization` (`DataclassSerializer`/`to_dict`) with no bespoke per-type serializer.
- [x] `OptimizationRunRepository` implemented as `type OptimizationRunRepository = BaseRepository[OptimizationRun, str]` — a type alias, **not** a new ABC or subclass.
- [x] Reference implementation uses `core.InMemoryRepository[OptimizationRun, str]()` directly, with zero new persistence code.
- [x] Test suite for `OptimizationRunRepository` behavior written against the `core.BaseRepository[OptimizationRun, str]` contract alone, never against `InMemoryRepository`-specific internals (§35's repository-substitutability proof).

## Versioning (§25)

- [x] `OptimizationMetadata.version` (a registered model *type*'s own SemVer) and `OptimizationProblem.version` (a governed configuration artifact's own SemVer) confirmed to vary independently — no code path derives one from another.
- [x] `OptimizationVersionConflictError` raised at registration time for a materially-different re-registration under an existing `OptimizationMetadata.code`; `ProblemConflictError` raised at publication time for the equivalent `OptimizationProblem` case — both never deferred.

## Caching (§26)

- [x] Confirmed no dedicated `OptimizationStateCache`-style module exists anywhere in the package (§26's documented, deliberate non-need; §34's recorded anti-pattern against introducing one "for consistency").
- [x] Confirmed `OptimizationContext` assembly happens once, at construction, never re-fetched per-solve or per-iteration (§36).

## Validation (§27)

- [x] `OptimizationMetadata.validate()` — non-empty `code`, category matches the closed `OptimizationCategory` namespace.
- [x] `OptimizationProblem.validate()` — non-empty `code`/`model_code`; non-empty `objectives`/`variables`; objective-count-vs-category rule (§14); variable-domain-vs-category rule (§11).
- [x] `OptimizationState.validate()` — non-empty `attributes`.
- [x] Each `OptimizationModel` category subclass's own namespace-convention check implemented.

## Error Handling (§28)

- [x] Full exception hierarchy (design spec §6 `exceptions.py`): `OptimizationValidationError`, `OptimizationRunNotFoundError`, `OptimizationExecutionError`, `OptimizationVersionConflictError`, `ProblemConflictError` — each subclassing the matching `core` exception.
- [x] Confirmed no `OptimizationModel` category method raises for a legitimately infeasible problem — returns an `OptimizationResult` carrying `feasible=False` and a warning instead.

## Metadata (§29)

- [x] `OptimizationCategory` enum (§29) — exactly `LinearProgramming`/`MixedIntegerProgramming`/`ConstraintProgramming`/`MultiObjective`/`EvolutionaryMetaheuristic`/`NetworkOptimization`; a closed enum, adding a member is a governance-reviewed change.
- [x] `OptimizationMetadata` (§29) — `code`, `category`, `description`, `version` (default `"1.0.0"`); `validate()` rejects an empty `code`.
- [x] Confirmed `OptimizationMetadata.code` names a model **type** and is never confused with an `OptimizationRun.id` anywhere in the codebase.

## Thread Safety & Concurrency (§32, §33)

- [x] `OptimizationModel` instances (of every category) confirmed stateless and safe to share/read across threads with no locking.
- [x] `OptimizationRun` instances confirmed immutable and safe to share/read across threads with no locking.
- [x] `OptimizationRunRepository`'s per-id write serialization contract documented and tested against any production-grade implementation candidate; confirmed the bare `core.InMemoryRepository` reference implementation provides **no** locking of its own — any concurrent-write test against it must add external synchronization itself.
- [x] `optimization.REGISTRY` confirmed read-only and thread-safe after startup discovery, inheriting `Registry`'s own contract.
- [x] Independent `OptimizationRun`s (different `id`s) proven to execute fully in parallel without contention.
- [x] Reproducibility proven: identical seeds to `EvolutionaryMetaheuristicModel._iterate` produce identical `OptimizationState` trajectories, independent of execution order.

## Tests

- [x] `tests/unit/optimization/` mirrors `src/mineproductivity/optimization/` 1:1.
- [x] Coverage ≥95%.
- [x] Unit tests per concrete model category — at least one flagship model per category, each against a scripted problem with a known, hand-computed optimal solution (§35).
- [x] Reproducibility tests, identity/equality tests, infeasibility tests, delegation tests, registry/discovery isolation tests, interface-only ABC contract tests, `simulation.ExperimentRunner` composition tests, and concurrency stress tests as enumerated in design spec §35.
- [x] The six package acceptance proofs in design spec §35 (no-fact-recomputation, no-statistics-reimplementation, immutability, interface-purity, no-architectural-drift, no-solver-coupling) each independently verified and recorded in the PR description.

## Documentation

- [x] `optimization/README.md` complete.
- [x] Every registered `OptimizationModel` type's docstring restates its `OptimizationMetadata.description` for source-level readability.

## Examples

- [x] `examples/optimization/01_mip_fleet_allocation.py` — the design spec §17-adjacent worked example (a MIP-category fleet/shift allocation problem seeded from a `TwinSnapshot`), end-to-end.
- [x] `examples/optimization/02_plan_comparison.py` — `PlanComparator` composed over two named problems' solved outcomes.
- [x] `examples/optimization/03_sensitivity_sweep.py` — `SensitivityAnalyzer.sweep()` over a single constraint bound.
- [x] `examples/optimization/04_candidate_scenario_search.py` — a search over candidate `simulation.Scenario`s via `simulation.ExperimentRunner`, compared with `PlanComparator`.
- [x] `examples/optimization/05_plugin_solver_adapter.py` — a third-party-style category-ABC subclass registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern.
- [x] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [x] `OptimizationRunRepository.get()`/`list()` latency at representative run-population scale, recorded in `benchmark/reports/optimization/`.
- [x] A post-optimality sweep's parallel-re-solve throughput at representative sweep-value counts, recorded.

## Certification

- [x] Design spec §35's six package acceptance proofs pass and are recorded in the PR description (duplicated here from Tests for merge-gate visibility).

## Type Hints, Mypy, Ruff, Coverage

- [x] 100% type-hinted; `mypy --strict` clean.
- [x] `ruff check` and `ruff format --check` clean.
- [x] Coverage report attached; ≥95%.

## Release

- [x] `CHANGELOG.md` updated.
- [x] Root README dependency diagram cross-checked — confirm no forbidden import (`agents`, `visualization`) was introduced, and confirm no lower package gained a new `optimization` import.
- [x] Version bump proposed and reviewed.
- [x] Design spec §35's acceptance proofs re-verified as final merge gate.

---

*Derived from [`10_Optimization_Design_Specification.md`](../architecture/10_Optimization_Design_Specification.md). Keep in sync with the governing specification and with [`ADR-0010-Optimization.md`](../adr/ADR-0010-Optimization.md).*
