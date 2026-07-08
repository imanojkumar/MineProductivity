# Roadmap

MineProductivity's overall architecture (Master Architecture Handbook v1.0) is
locked and documentation-complete. The software implementing it is versioned
independently via [Semantic Versioning](https://semver.org/); the current
software release is `1.7.0` (see [`CHANGELOG.md`](CHANGELOG.md) for the full
milestone history). This roadmap tracks implementation phases against the
Reference Implementation Blueprint v1.0 and reflects the repository's actual,
current state — not a plan for a future not-yet-executed sequence.

Each phase below is one of three states: **Implemented** (real code, tested,
merged), **Architecture Complete** (a locked Design Specification,
Implementation Checklist, and ADR exist; no production code yet), or **Not
Started** (neither exists yet).

## Phase 0 — Repository Skeleton

**Status: Complete.**

- Full directory structure for `src/`, `tests/`, `docs/`, `datasets/`,
  `notebooks/`, `examples/`, `benchmark/`, `certification/`, `scripts/`.
- Packaging, governance, and CI/CD placeholders.
- Zero business logic.

## Phase 1 — Foundation Layer

**Status: Partially implemented.**

- `core` — **Implemented.** Base entities, value objects, identifiers.
- `ontology` — **Implemented.** Domain vocabulary and schema definitions.
- `registry`, `plugins` — **Implemented.** Extension mechanisms.
- `exceptions`, `config`, `utils`, `io` — **Not started.** Cross-cutting
  primitives; each remains a structural placeholder. (`core` defines its own
  internal exception hierarchy directly and does not currently depend on the
  separate top-level `exceptions` package.)

## Phase 2 — Event & KPI Layer

**Status: Partially implemented.**

- `events` — **Implemented.** Event schema, event store, event bus,
  replay/time-travel.
- `kpis` — **Implemented.** KPI metadata model and the standard KPI library
  (per Developer & Cookbook Guide — Part III).
- `validation` — **Not started.** Schema and data-quality validation
  framework; remains a structural placeholder.

## Phase 3 — Data & Connectivity Layer

**Status: Partially implemented.**

- `connectors` — **Implemented.** Source-system integration interfaces and
  six reference connectors, plus five documentation-only OEM adapter shapes.
- `datasets` — **Not started.** Dataset abstractions and canonical/golden
  dataset loaders; remains a structural placeholder. (The implemented `kpis`
  package uses its own, separate `tests/fixtures/kpis` sample-dataset loader
  in the meantime.)

## Phase 4 — Analytical Layer

**Status: Implemented for `analytics`; Architecture complete for
`simulation` and `optimization`.**

- `analytics` — **Implemented** (v1.5.0 milestone, architecture approved at
  the v0.8.0 milestone). Statistical and analytical processing built on
  `kpis`/`events` — trend, baseline, and benchmark analysis, rolling and
  aggregate statistics, data-quality scoring, batch/streaming/incremental
  execution modes, and a self-registering plugin registry; interface-only
  forecasting/anomaly/outlier-detection models (zero concrete subclasses by
  design, see `ADR-0006-Analytics-Engine.md`).
- `simulation` — **Architecture complete** (v1.1.0 milestone). Scenario
  management, `SimulationRun` execution, interface-only Monte Carlo/
  discrete-event/system-dynamics/calibration models, experiment
  orchestration, scenario comparison and sensitivity analysis (delegated to
  `analytics`). See
  [`docs/architecture/09_Simulation_Design_Specification.md`](docs/architecture/09_Simulation_Design_Specification.md).
- `optimization` — **Architecture complete** (v1.2.0 milestone). Solved-plan
  search over six interface-only paradigms (linear programming, mixed-integer
  programming, constraint programming, multi-objective, evolutionary/
  metaheuristic, network optimization), plan comparison and sensitivity
  analysis (delegated to `analytics`). See
  [`docs/architecture/10_Optimization_Design_Specification.md`](docs/architecture/10_Optimization_Design_Specification.md).

## Phase 5 — Decision & Twin Layer

**Status: `decision` and `digital_twin` fully implemented; Architecture
complete for `agents`.**

- `decision` — **Fully implemented** (Phases 07.1-07.4, architecture
  approved at the v0.9.0 milestone; software release v1.6.0).
  Decision-support and recommendation frameworks that translate
  `analytics`' statistical judgments into actionable, explained
  recommendations. `DecisionModel`/`DecisionContext`, `DecisionMetadata`/
  `DecisionCategory`, the full `DecisionResult` family,
  `DecisionPipeline`/`PipelineStage`/`ModelStage`, and the `REGISTRY`/
  `register` plugin mechanism (07.1); rule composition/evaluation
  (`Rule`, `RuleEngine`, `RuleEngineStage`), versioned policy governance
  (`Policy`, `DecisionStatus`), and the default, concrete
  `ThresholdDecisionStrategy` with real threshold-breach evaluation
  (07.2); `DecisionScorer`/`ConfidenceScorer`, `RankingStrategy`/
  `WeightedScoreRanking`, `ExplanationBuilder`/`ExplanationStage`,
  `ActionPrioritizer`, and the interface-only `RootCauseAnalyzer` (07.3);
  and the interface-only `WhatIfEngine`, `ActionPlanner`,
  `AlertGenerator`, `RealTimeDecisionSession`/`BatchDecisionRunner`, and
  `DecisionAuditTrail`/`DecisionAuditEntry` (07.4) are all implemented.
  `decision` is now feature-complete per the Reference Implementation
  Blueprint's design spec §6 module list (see
  `src/mineproductivity/decision/README.md`).
- `digital_twin` — **Fully implemented** (architecture approved at the
  v1.0.0 milestone; software release v1.7.0). The platform's stateful
  representation layer — `Twin` (a `core.BaseEntity[str]` subclass, the
  first entity-shaped central abstraction in the series)/`TwinContext`,
  `TwinMetadata`/`TwinCategory`, the eleven twin category base classes,
  `TwinStatus`, `TwinState`/`TwinSnapshot`, `TwinSynchronizer`/
  `SyncPolicy` (live `EventBus` subscription and cold-start
  `EventStore.replay` reconstruction, provably convergent),
  `TelemetryReading`, the interface-only `TwinSimulationModel` (zero
  concrete subclasses by design), `by_category`/`by_scope` discovery,
  `TwinRepository` as a literal type alias over
  `core.BaseRepository[Twin, str]`, `TwinStateCache`, the
  `TwinResult`/`SyncResult`/`TwinSimulationResult` family, and the
  `REGISTRY`/`register` plugin mechanism. `digital_twin` is
  feature-complete per the Reference Implementation Blueprint's design
  spec §6 module list (see
  `src/mineproductivity/digital_twin/README.md`).
- `agents` — **Architecture complete** (v1.3.0 milestone). Model-independent
  agent orchestration layer — `Agent`/`Tool`/`AgentMemory` interfaces, task
  lifecycle, policy engine, human approval workflows, multi-agent
  delegation. See
  [`docs/architecture/11_AI_Agents_Design_Specification.md`](docs/architecture/11_AI_Agents_Design_Specification.md).

## Phase 6 — Experience Layer

**Status: Architecture complete for `visualization`; not started for `cli`.**

- `visualization` — **Architecture complete** (v1.4.0 milestone). The
  platform's final package — dashboards, reports, and rendering-backend-
  independent presentation of every lower package's already-structured
  output. See
  [`docs/architecture/12_Visualization_Design_Specification.md`](docs/architecture/12_Visualization_Design_Specification.md).
- `cli` — command-line interface. No architecture specification exists yet.

## Phase 7 — Quality & Certification

**Status: Not started** (as packages; lightweight standalone substitutes
already exist under `scripts/quality/`).

- `benchmark` — conformance/reference benchmark scenarios and reporting as a
  package remain a structural placeholder; `scripts/quality/perf_smoke.py`
  already provides a lightweight, standalone performance smoke test used by
  CI in the meantime.
- `certification` — conformance test suite and reference output validation;
  remains a structural placeholder.
- A `1.0`-line software release milestone tagged specifically for
  "Reference Implementation Blueprint fully satisfied, certification suite
  passing" has not yet been reached — see Versioning Policy below for how
  this differs from the software's own SemVer track, which has already
  passed `1.0.0` for unrelated reasons.

## Future Architecture Proposals

Entries here are **proposals, not phases**: no Design Specification,
Implementation Checklist, or ADR exists for them, they are not scheduled, and
no code may be written against them. They are recorded so the intent survives
until their revisit trigger is reached.

### Analytics Maturity Assessment (post-v2.0)

- **What:** An analytics maturity assessment framework for mining
  enterprises — structured maturity scoring that helps leadership prioritize
  AI investments, quantify business-value assurance, accelerate digital
  transformation initiatives, and support governance.
- **Status:** Proposal only, captured July 2026 (software v1.6.0).
  Explicitly out of scope for every phase above.
- **Revisit trigger:** Only after the MineProductivity core platform is
  complete (the Reference Implementation Blueprint phases above reach
  **Implemented**).
- **Deferred packaging decision:** Either a separate package (e.g.
  `mineproductivity.assessment`) or an application built on top of the
  framework. The locked architecture names `visualization` as the final
  package in the platform's dependency chain, so the package option would
  require an explicit architecture amendment, while the application option
  leaves the locked chain untouched. Neither option is chosen yet; the
  evaluation belongs to the revisit, not to any current phase.

## Versioning Policy

- **Architecture documents** are versioned independently and are already
  locked at `v1.0` (Master Architecture Handbook, Reference Implementation
  Blueprint).
- **Software** follows [Semantic Versioning](https://semver.org/), starting
  at `0.1.0`. The single authoritative source is
  [`src/mineproductivity/__init__.py`](src/mineproductivity/__init__.py)'s
  `__version__`; `pyproject.toml` reads it dynamically and nothing else
  should hardcode it (tests compare against installed package metadata
  instead — see `tests/unit/core/test_public_api.py`).
- In practice, this repository has bumped the software's MINOR version once
  per completed architecture or implementation milestone (`v0.7.0` KPI Engine
  through `v1.6.0` Decision Intelligence implementation) — a deliberate,
  precedented convention distinct from waiting for a certification-gated
  `1.0` release. Under this convention, the
  software's SemVer track and the "Phase 7 certification-gated 1.0"
  milestone described above are two different concepts that happen to share
  the digit `1.0`: the software already carries a version number at or past
  `1.0.0`, while the certification-gated milestone Phase 7 describes has not
  been reached. A future decision may rename or otherwise reconcile this
  overlap; until then, treat "software version" (SemVer, `CHANGELOG.md`) and
  "Reference Implementation Blueprint completion" (this roadmap's phases) as
  two independently-tracked measures of progress, not one.
