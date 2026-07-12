# mineproductivity.simulation

## Purpose

Simulation engines for projecting a mining system's state forward under a hypothetical or historical scenario — orchestrating pluggable Monte Carlo, discrete-event, system-dynamics, and calibration models, seeded from real `digital_twin` snapshots and event history, without owning KPI computation, statistics, or decision logic itself. The package `digital_twin` spec 08 §14 named as `TwinSimulationModel`'s most direct anticipated implementer, and — by composing that implementation — positioned to become the first concrete provider of `decision.WhatIfEngine`.

## Scope

**What belongs here:**
- Simulation engine interfaces and scenario contracts.
- Scenario governance, run execution/orchestration, experiment management, and the delegation seams (`ScenarioComparator`/`SensitivityAnalyzer`) that hand statistical questions to `analytics`.

**What must never belong here:**
- Live digital twin state management (see `digital_twin`).
- Optimization solving (see `optimization`).
- Descriptive/inferential statistics of any kind (see `analytics` — design spec §3.2, §35's no-statistics-reimplementation proof).
- A concrete Monte Carlo, discrete-event, system-dynamics, or calibration algorithm (interface-only by design, §13–§16, ADR-0009).

## Responsibilities

- Implements the `simulation` subsystem as defined in the Reference Implementation Blueprint v1.0 — the complete design spec §6 module list (twenty-one modules), in one implementation phase. `SimulationModel` (§8) deliberately carries no shared abstract execution method — Monte Carlo trials, discrete-event scheduling, and system-dynamics integration are structurally different enough that each category base declares its own (`_trial`/`_advance`/`_step`), and `CalibrationModel` is deliberately not a `SimulationModel` subclass at all. `Scenario` (§9) is the package's governed artifact — versioned, publish/supersede-gated (`ScenarioConflictError`), reusing `digital_twin.TwinSnapshot` for real-history starting conditions and `events.AsOf` for the scenario hook `decision.WhatIfEngine` was designed around. `SimulationRun` (§10) is the series' second entity-shaped abstraction, following `digital_twin.Twin`'s `core.BaseEntity[str]`/`with_state()` precedent exactly; statefulness lives entirely in the run, never in a model. `SimulationExecutor` (§10) dispatches by registered `SimulationCategory` — never by concrete Python type — validates the injected `SimulationClock`'s `TimeProgressionMode` against the category, seeds from snapshot/cached-replay/provisioned state, and persists every produced state through the repository swap; `Completed`/`Failed` are terminal. `seed_from_replay` (§12) is a thin wrapper over `events.EventStore.replay` — no second replay mechanism. `ExperimentRunner` (§17) dispatches trials concurrently with per-trial `random_seed`s (§33's reproducibility anchor); `SensitivityAnalyzer.sweep` (§20) is structurally a specialized experiment reusing that machinery. `ScenarioComparator`/`SensitivityAnalyzer.summarize` delegate every statistical judgment to `analytics.describe`/`distribution`/`confidence_interval` (§19–§20). `SimulationRunRepository` (§24) is a literal `type` alias over `core.BaseRepository[SimulationRun, str]`; `SimulationStateCache` (§26) caches replay seeds per `(scenario_code, as_of)` — never authoritative for run state. `REGISTRY`/`register` (§21) specialize `registry.Registry` exactly as every sibling package does; the package ships zero registered built-in models by design.

## Contents

- `__init__.py` — public API surface (34 symbols, the full design spec §7 list).
- `abstractions.py` — `SimulationModel` (ABC), `SimulationContext`.
- `metadata.py` — `SimulationMetadata`, `SimulationCategory`.
- `scenario.py` — `Scenario`, `ScenarioStatus` (plus the internal `publish_scenario` governance function; see its module docstring for the disclosed non-export).
- `run.py` — `SimulationRun` (`core.BaseEntity[str]`, concrete), `RunStatus`.
- `state.py` — `SimulationState`.
- `clock.py` — `SimulationClock`, `TimeProgressionMode`.
- `replay.py` — `seed_from_replay()`.
- `montecarlo.py` / `discrete_event.py` / `system_dynamics.py` — `MonteCarloModel`/`DiscreteEventModel`/`SystemDynamicsModel` (ABCs, interface only — zero concrete subclasses).
- `calibration.py` — `CalibrationModel` (ABC, interface only — not a `SimulationModel` subclass).
- `executor.py` — `SimulationExecutor`.
- `experiment.py` — `Experiment`, `ExperimentRunner`.
- `comparison.py` — `ScenarioComparator`.
- `sensitivity.py` — `SensitivityAnalyzer`.
- `discovery.py` — `by_category()`, `by_scope()` specification factories.
- `persistence.py` — `SimulationRunRepository` (`type` alias over `core.BaseRepository[SimulationRun, str]`).
- `caching.py` — `SimulationStateCache`.
- `result.py` — `SimulationResult`, `ExperimentResult`.
- `_registry.py` — `REGISTRY`, `register`.
- `exceptions.py` — the package's exception hierarchy.
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `events`, `registry`, `kpis`, `analytics`, `decision`, `digital_twin` (currently exercised — `analytics` especially heavily, as the statistical engine `ScenarioComparator`/`SensitivityAnalyzer` delegate to entirely); `ontology`, `plugins`, `connectors` are permitted under the platform-wide layering rule — `ontology` supplies vocabulary only, `plugins` orchestrates entry-point discovery at the application level, and `connectors` is deliberately never exercised: simulation operates on already-computed, already-event-sourced, already-synchronized facts, never a vendor-specific wire format (design spec §5).

**Depended on by:** `optimization`, `agents`, `visualization`

## Future Work

`simulation` is feature-complete per the Reference Implementation Blueprint's design spec §6 module list. Future work is limited to: the first concrete `MonteCarloModel`/`DiscreteEventModel`/`SystemDynamicsModel`/`CalibrationModel` plugins (first-party or third-party, per §30 — deliberately never shipped inside this package itself, §34; `optimization` is named as `CalibrationModel`'s most plausible first implementer, §37), the first concrete `decision.WhatIfEngine` composed from a `TwinSimulationModel`-conforming model and `SimulationExecutor` (the two-hop bridge specs 07/08 both anticipated), new `Scenario` authoring (a governed, no-code-change extension, §30.3), a production-grade `SimulationRunRepository` backend (§30.5), and whatever `optimization`/`agents`/`visualization` need from this package as those packages move from architecture-complete to implemented (§37).

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- [`docs/architecture/09_Simulation_Design_Specification.md`](../../../docs/architecture/09_Simulation_Design_Specification.md)
- [`docs/adr/ADR-0009-Simulation.md`](../../../docs/adr/ADR-0009-Simulation.md)
