# Simulation — Implementation Checklist

**Package:** `mineproductivity.simulation`
**Governing specification:** [`docs/architecture/09_Simulation_Design_Specification.md`](../architecture/09_Simulation_Design_Specification.md)
**Architecture Decision Record:** [`docs/adr/ADR-0009-Simulation.md`](../adr/ADR-0009-Simulation.md)
**Status:** Not started

Binding, **locked** implementation contract for `simulation` — the fourth package built on top of the Foundation Layer, sitting directly above the now-locked `digital_twin`. Nothing described here may be implemented before this checklist and its governing specification exist in reviewed form, and nothing may be implemented that is not represented by an item on this list. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [ ] Design specification (`09_Simulation_Design_Specification.md`) read in full by the implementer, including every cross-reference to specs 01–08.
- [ ] ADR-0009 read in full; the rationale for `simulation` existing as a separate package above `digital_twin` (and for the interface-only treatment of Monte Carlo, discrete-event, system-dynamics, and calibration methodologies) is understood, not merely accepted.
- [ ] `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, `kpis`, `analytics`, `decision`, `digital_twin` available and importable, exactly as released; no lower package file is modified as a side effect of this work.
- [ ] Confirmed: `simulation` will not import `optimization`, `agents`, or `visualization` under any circumstance — none of those packages exist yet (design spec §5, §37).
- [ ] Confirmed: no lower package (`core` through `digital_twin`) will be modified to import or otherwise reference `simulation` (design spec §5).

## Package Structure

- [ ] `src/mineproductivity/simulation/` created matching design spec §6 exactly: `abstractions.py`, `metadata.py`, `scenario.py`, `run.py`, `state.py`, `clock.py`, `replay.py`, `montecarlo.py`, `discrete_event.py`, `system_dynamics.py`, `calibration.py`, `executor.py`, `experiment.py`, `comparison.py`, `sensitivity.py`, `discovery.py`, `persistence.py`, `caching.py`, `result.py`, `_registry.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [ ] `simulation/README.md` written following the `core/README.md` template.
- [ ] Confirmed `montecarlo.py`, `discrete_event.py`, `system_dynamics.py`, and `calibration.py` each contain zero concrete, non-test subclasses of `MonteCarloModel`/`DiscreteEventModel`/`SystemDynamicsModel`/`CalibrationModel` (mechanical grep/AST check — design spec §13–§16, §35's interface-purity proof).
- [ ] Confirmed no module under `src/mineproductivity/simulation/` performs direct KPI, statistical, decision, or twin-state computation of its own — every such value arrives via the corresponding lower package's public API (design spec §3.2, §35's no-fact-recomputation proof).
- [ ] Confirmed `comparison.py`/`sensitivity.py` contain zero direct mean/percentile/correlation arithmetic — every such computation is a call into `analytics` (design spec §35's no-statistics-reimplementation proof).

## Public API

- [ ] `simulation/__init__.py` exports exactly the symbol list in design spec §7, alphabetized `__all__`.
- [ ] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py` and every existing package's own copy of it.
- [ ] `TestNoForbiddenDependencies` AST-walks every `simulation` submodule for a forbidden import (`optimization`, `agents`, `visualization`) — mirrors every existing package's own copy of this test (design spec §5).
- [ ] A second, reverse-direction test asserts no file under `src/mineproductivity/{core,ontology,events,registry,plugins,connectors,kpis,analytics,decision,digital_twin}/` imports `mineproductivity.simulation` (design spec §5) — the `analytics`/`decision`/`digital_twin`-package precedent for this test extended one layer up.

## Simulation Abstractions (§8)

- [ ] `SimulationModel` (§8) — `meta: ClassVar[SimulationMetadata]`; deliberately no shared abstract execution method.
- [ ] `SimulationContext` (§8) — `event_store`, `kpi_results`, `analytics_results`, `decision_results`, each defaulting to an empty sequence.
- [ ] Confirmed `SimulationModel` subclasses (of every category) are stateless — no instance attribute is mutated by any category method (§29, §32).
- [ ] `CalibrationModel` (§16) confirmed **not** a `SimulationModel` subclass anywhere in the codebase.

## Scenario Management (§9)

- [ ] `ScenarioStatus` enum (§9) — exactly `Proposed`/`Active`/`Superseded`/`Retired`.
- [ ] `Scenario` (§9) — frozen `core.BaseValueObject`; `code`, `version` (default `"1.0.0"`), `status`, `model_code`, `parameters`, `time_horizon`, `initial_state` (`TwinSnapshot | None`), `as_of` (`AsOf | None`); `validate()` rejects an empty `code` or `model_code`.
- [ ] Confirmed an `Active` `Scenario` is never edited in place anywhere in the codebase — a changed scenario is published as a new version, with the prior version transitioned to `Superseded` (§9, §25, §34's recorded anti-pattern).
- [ ] `ScenarioConflictError` raised for a materially-different re-registration under an existing, `Active` scenario code without a version bump (§9, §25).

## Simulation Execution (§10)

- [ ] `RunStatus` enum (§10) — exactly `Scheduled`/`Running`/`Paused`/`Completed`/`Failed`.
- [ ] `SimulationRun` (§10) — subclasses `core.BaseEntity[str]` directly; `scenario_code`, `state: SimulationState`, `status: RunStatus`; `with_state()` non-overridden, produces a new instance via `dataclasses.replace`, never mutates `self`.
- [ ] Identity/equality proven: `SimulationRun.__eq__`/`__hash__` inherited unchanged from `BaseEntity` (identity-based on `id`, ignoring `state`/`status`); no override anywhere in the package.
- [ ] Lifecycle transitions proven to match design spec §10's state diagram exactly; `Completed` and `Failed` proven terminal (no transition out of either).
- [ ] `SimulationExecutor` (§6, §10) — dispatches to the registered `SimulationModel`'s category-specific method (`_trial`/`_advance`/`_step`) based on the `Scenario.model_code`'s registered `SimulationCategory`, never by branching on the model's concrete Python type; advances `SimulationClock`; persists the resulting state via a `remove`-then-`add` pair against `SimulationRunRepository`.
- [ ] `SimulationExecutor`'s dispatch and persistence sequence tested against design spec §10's sequence diagram exactly, including the cache-hit and cache-miss seeding paths (§26).

## Time Progression and Event Replay (§11, §12)

- [ ] `TimeProgressionMode` enum (§11) — exactly `FixedTimestep`/`NextEvent`/`TrialBased`.
- [ ] `SimulationClock` (§11) — `mode`, optional `dt`; `advance(current, *, delta=None)`; confirmed to hold no dependency on any specific `SimulationModel` category.
- [ ] `seed_from_replay()` (§12) implemented as a thin wrapper over `events.EventStore.replay(as_of)`; confirmed no second replay mechanism exists anywhere in the package.
- [ ] `seed_from_replay()` proven to reconstruct the identical `SimulationState` a hand-computed fold over the same event history would produce (§12, §35).

## Monte Carlo, Discrete Event, System Dynamics, Calibration Interfaces (§13–§16)

- [ ] `MonteCarloModel` (§13) — `_trial(scenario, *, context, random_seed) -> SimulationResult` abstract; zero concrete subclasses shipped.
- [ ] `DiscreteEventModel` (§14) — `_advance(state, *, context) -> tuple[SimulationState, timedelta]` abstract; zero concrete subclasses shipped.
- [ ] `SystemDynamicsModel` (§15) — `_step(state, *, context, dt) -> SimulationState` abstract; zero concrete subclasses shipped.
- [ ] `CalibrationModel` (§16) — `_calibrate(model_code, ground_truth, *, context) -> Mapping[str, Any]` abstract; `ground_truth` typed as `Sequence[TwinSnapshot]`; zero concrete subclasses shipped.
- [ ] Confirmed no concrete `MonteCarloModel` implementation anywhere in the test suite holds mutable random-number-generator state across `_trial` calls — every trial's randomness derives solely from the supplied `random_seed` (§33, §34's recorded anti-pattern).
- [ ] Reproducibility proven mechanically: identical `random_seed` inputs to `MonteCarloModel._trial` produce identical outputs, verified across every registered Monte Carlo model in the test suite (§35's reproducibility proof).

## Experiment Management (§17)

- [ ] `Experiment` (§17) — frozen `core.BaseValueObject`; `name`, `scenario`, `run_ids: tuple[str, ...]`.
- [ ] `ExperimentRunner` (§17) — composes `SimulationExecutor` for each individual run rather than duplicating its dispatch/persistence logic; `run_trials(scenario, *, trials, context) -> Experiment`.
- [ ] Confirmed independent `SimulationRun`s (different `id`s) execute fully in parallel with no contention; `ExperimentRunner` dispatches trials concurrently in the reference implementation (§33).
- [ ] The design spec §17 worked example (500-trial Monte Carlo experiment seeded from a `digital_twin.TwinSnapshot`) reproduced end-to-end as an integration test.

## Simulation Outputs, Scenario Comparison, Sensitivity Analysis (§18, §19, §20)

- [ ] `SimulationResult` (§18) — frozen `core.BaseValueObject`; `run_id`, `computed_at`, `warnings`, `final_state`.
- [ ] `ExperimentResult` (§18) — subclasses `SimulationResult`; adds `trial_results: tuple[SimulationResult, ...]`; confirmed to perform no statistical characterization of `trial_results` itself.
- [ ] Confirmed `SimulationState` is **not** a `SimulationResult` subclass (it represents the run's condition itself, not the outcome of an orchestration call about it).
- [ ] `ScenarioComparator.compare()` (§19) implemented; confirmed every comparison delegates to `analytics.describe()`/`StatisticalSummary` — no mean/percentile computation exists in this package's own code.
- [ ] `SensitivityAnalyzer.sweep()` (§20) implemented; confirmed every sweep hands its `SimulationResult`s to `analytics`' `DistributionSummary`/`confidence_interval` for distributional treatment — no correlation/regression computation exists in this package's own code.
- [ ] Delegation tests assert the actual `analytics` primitive invoked by `ScenarioComparator`/`SensitivityAnalyzer` (e.g. `describe`), never re-derive the expected statistic independently inside the test (§35).

## Simulation Registry and Discovery (§21, §22)

- [ ] `simulation._registry.REGISTRY`/`register` (§21) — `Registry[str, type[SimulationModel]]`, raising `SimulationValidationError` for an empty code and `SimulationVersionConflictError` for a materially-different re-registration under an existing code.
- [ ] `EntryPointSpec(group="mineproductivity.simulation", target_registry="simulation")` discovery wired via `registry.EntryPointDiscovery` (§31).
- [ ] `by_category()`/`by_scope()` (§22) — plain `core.PredicateSpecification` factories; composed with `SimulationRunRepository.list()`; confirmed to return an empty sequence (never raise) for a filter matching nothing.
- [ ] Confirmed the three-way distinction (`REGISTRY` = which model types are known; `SimulationRunRepository` = which run instances currently exist; `discovery.py` = query facade over the instance store) is never conflated anywhere in the codebase (§21).

## Serialization and Persistence (§23, §24)

- [ ] Every `SimulationState`/`Scenario`/`SimulationResult` subclass and `SimulationRun` itself confirmed to serialize via `core.serialization` (`DataclassSerializer`/`to_dict`) with no bespoke per-type serializer.
- [ ] `SimulationRunRepository` implemented as `type SimulationRunRepository = BaseRepository[SimulationRun, str]` — a type alias, **not** a new ABC or subclass.
- [ ] Reference implementation uses `core.InMemoryRepository[SimulationRun, str]()` directly, with zero new persistence code.
- [ ] Test suite for `SimulationRunRepository` behavior written against the `core.BaseRepository[SimulationRun, str]` contract alone, never against `InMemoryRepository`-specific internals (§35's repository-substitutability proof).

## Versioning (§25)

- [ ] `SimulationMetadata.version` (a registered model *type*'s own SemVer) and `Scenario.version` (a governed configuration artifact's own SemVer) confirmed to vary independently — no code path derives one from another.
- [ ] `SimulationVersionConflictError` raised at registration time for a materially-different re-registration under an existing `SimulationMetadata.code`; `ScenarioConflictError` raised at publication time for the equivalent `Scenario` case — both never deferred.

## Caching (§26)

- [ ] `SimulationStateCache.get()`/`put()` (§26) implemented, keyed by `(scenario_code, as_of)`.
- [ ] Confirmed **not** a reuse of `kpis.ResultCache` or `digital_twin.TwinStateCache` — cache key shape independently designed for replay-seeded simulation state, not KPI-result or twin-evidence semantics.
- [ ] Confirmed a cache miss (`get()` returning `None`) never raises and always falls back to `seed_from_replay()` directly.
- [ ] Confirmed `SimulationExecutor`/`ExperimentRunner` never treat `SimulationStateCache` as authoritative for "what is this run's current state" — only `SimulationRunRepository` is.

## Validation (§27)

- [ ] `SimulationMetadata.validate()` — non-empty `code`, category matches the closed `SimulationCategory` namespace.
- [ ] `Scenario.validate()` — non-empty `code` and `model_code`.
- [ ] `SimulationState.validate()` — non-empty `attributes`.
- [ ] Each `SimulationModel` category subclass's own namespace-convention check implemented.

## Error Handling (§28)

- [ ] Full exception hierarchy (design spec §6 `exceptions.py`): `SimulationValidationError`, `SimulationRunNotFoundError`, `SimulationExecutionError`, `SimulationVersionConflictError`, `ScenarioConflictError` — each subclassing the matching `core` exception.
- [ ] Confirmed no `SimulationModel` category method raises for a legitimately incomplete input (e.g. zero trials requested) — returns a `SimulationResult`/`Experiment` carrying a warning instead.

## Metadata (§29)

- [ ] `SimulationCategory` enum (§29) — exactly `MonteCarlo`/`DiscreteEvent`/`SystemDynamics`/`Calibration`; a closed enum, adding a member is a governance-reviewed change.
- [ ] `SimulationMetadata` (§29) — `code`, `category`, `description`, `version` (default `"1.0.0"`); `validate()` rejects an empty `code`.
- [ ] Confirmed `SimulationMetadata.code` names a model **type** and is never confused with a `SimulationRun.id` anywhere in the codebase.

## Thread Safety & Concurrency (§32, §33)

- [ ] `SimulationModel` instances (of every category) confirmed stateless and safe to share/read across threads with no locking.
- [ ] `SimulationRun` instances confirmed immutable and safe to share/read across threads with no locking.
- [ ] `SimulationRunRepository`'s per-id write serialization contract documented and tested against any production-grade implementation candidate; confirmed the bare `core.InMemoryRepository` reference implementation provides **no** locking of its own — any concurrent-write test against it must add external synchronization itself.
- [ ] `simulation.REGISTRY` confirmed read-only and thread-safe after startup discovery, inheriting `Registry`'s own contract.
- [ ] Independent `SimulationRun`s (different `id`s) proven to execute fully in parallel without contention; concurrent trials for the *same* run proven to serialize correctly (no lost update) once a conforming production `SimulationRunRepository` is used.
- [ ] `SimulationStateCache` reads/writes keyed by `(scenario_code, as_of)` proven non-contending across independent keys.

## Tests

- [ ] `tests/unit/simulation/` mirrors `src/mineproductivity/simulation/` 1:1.
- [ ] Coverage ≥95%.
- [ ] Unit tests per concrete model category — at least one flagship model per category, each against a scripted scenario with a known expected `SimulationState` trajectory (§35).
- [ ] Reproducibility tests, identity/equality tests, event-replay seeding tests, delegation tests, registry/discovery isolation tests, interface-only ABC contract tests, and concurrency stress tests as enumerated in design spec §35.
- [ ] The six package acceptance proofs in design spec §35 (no-fact-recomputation, no-statistics-reimplementation, immutability, interface-purity, no-architectural-drift, reproducibility) each independently verified and recorded in the PR description.

## Documentation

- [ ] `simulation/README.md` complete.
- [ ] Every registered `SimulationModel` type's docstring restates its `SimulationMetadata.description` for source-level readability.

## Examples

- [ ] `examples/simulation/01_monte_carlo_experiment.py` — the design spec §17 worked example (500-trial experiment seeded from a `TwinSnapshot`), end-to-end.
- [ ] `examples/simulation/02_scenario_comparison.py` — `ScenarioComparator` composed over two named scenarios' trial outcomes.
- [ ] `examples/simulation/03_sensitivity_sweep.py` — `SensitivityAnalyzer.sweep()` over a single `Scenario` parameter.
- [ ] `examples/simulation/04_plugin_simulation_model.py` — a third-party-style `SimulationModel` category subclass registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern.
- [ ] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [ ] `SimulationRunRepository.get()`/`list()` latency at representative run-population scale, recorded in `benchmark/reports/simulation/`.
- [ ] `SimulationStateCache` hit-rate and time saved across a representative Monte Carlo experiment's repeated trials, recorded.

## Certification

- [ ] Design spec §35's six package acceptance proofs pass and are recorded in the PR description (duplicated here from Tests for merge-gate visibility).

## Type Hints, Mypy, Ruff, Coverage

- [ ] 100% type-hinted; `mypy --strict` clean.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] Coverage report attached; ≥95%.

## Release

- [ ] `CHANGELOG.md` updated.
- [ ] Root README dependency diagram cross-checked — confirm no forbidden import (`optimization`, `agents`, `visualization`) was introduced, and confirm no lower package gained a new `simulation` import.
- [ ] Version bump proposed and reviewed.
- [ ] Design spec §35's acceptance proofs re-verified as final merge gate.

---

*Derived from [`09_Simulation_Design_Specification.md`](../architecture/09_Simulation_Design_Specification.md). Keep in sync with the governing specification and with [`ADR-0009-Simulation.md`](../adr/ADR-0009-Simulation.md).*
