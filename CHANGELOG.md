# Changelog

All notable changes to MineProductivity are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Note:** The software version (currently `1.8.0`) is independent of the
> architecture document version (`v1.0`, locked). The architecture is
> considered final for this phase; the software implementing it continues
> to evolve incrementally.

## [Unreleased]

## [1.8.0] - 2026-07-08

Simulation implementation milestone.

This release delivers the full production implementation of the
`mineproductivity.simulation` package against the architecture approved
in the `v1.1.0` milestone (Design Specification, Implementation
Checklist, and ADR-0009) — the platform's projection layer, built
directly on `digital_twin`, and the package both `decision` (spec 07
§19) and `digital_twin` (spec 08 §14, §34) named by anticipation. The
complete design spec §6 module list (twenty-one modules) ships in one
implementation phase.

### Added

- `SimulationModel` (ABC, deliberately no shared abstract execution
  method — each methodology declares its own) and `SimulationContext`,
  carrying `KPIResult`/`AnalyticsResult`/`DecisionResult` evidence
  read, never re-derived.
- `SimulationMetadata`/`SimulationCategory` (closed four-member enum)
  with import-time namespace/category conformance on every category
  base.
- `Scenario`/`ScenarioStatus` — the package's versioned, governed
  configuration artifact, reusing `digital_twin.TwinSnapshot` for
  real-history starting conditions and `events.AsOf` for the scenario
  hook `decision.WhatIfEngine` was designed around; publish/supersede
  governance with `ScenarioConflictError` raised at publication time.
- `SimulationRun` — the series' second `core.BaseEntity[str]`
  abstraction (identity-based equality inherited unchanged,
  `with_state()` producing new instances) — with `RunStatus`
  (`Completed`/`Failed` terminal) and `SimulationExecutor`:
  category-driven dispatch to `_trial`/`_advance`/`_step` (never
  branching on concrete type), clock-mode conformance validation,
  snapshot/cached-replay/provisioned seeding, per-step repository
  persistence, and `Failed`-marking on model errors.
- `SimulationState` (open attributes mapping + simulated time),
  `SimulationClock`/`TimeProgressionMode` (fixed-timestep, next-event,
  trial-based pacing), and `seed_from_replay` — a thin wrapper over
  `events.EventStore.replay`, no second replay mechanism.
- The four interface-only ABCs with zero concrete subclasses by design
  (ADR-0009): `MonteCarloModel` (`_trial`, seed-anchored
  reproducibility), `DiscreteEventModel` (`_advance`),
  `SystemDynamicsModel` (`_step`), and `CalibrationModel`
  (`_calibrate` over `TwinSnapshot` ground truth; deliberately not a
  `SimulationModel` subclass).
- `Experiment`/`ExperimentRunner` — concurrent trial dispatch with a
  distinct `random_seed` per trial; zero trials returns an empty
  experiment, never a raise.
- `ScenarioComparator`/`SensitivityAnalyzer` — thin orchestration
  layers delegating every statistical judgment to
  `analytics.describe`/`distribution`/`confidence_interval`;
  `sweep()` produces one run per swept value, ordered to match.
- `by_category`/`by_scope` discovery factories; `SimulationRunRepository`
  as a literal `type` alias over
  `core.BaseRepository[SimulationRun, str]`; `SimulationStateCache`
  keyed by `(scenario_code, as_of)`; the
  `SimulationResult`/`ExperimentResult` family; `REGISTRY`/`register`;
  and the full exception hierarchy.
- `examples/simulation/` — four runnable, `mypy --strict`/`ruff`-clean
  example scripts per the implementation checklist, including the
  design spec §17 worked example (a 500-trial Monte Carlo experiment
  seeded from a `TwinSnapshot`), also reproduced end-to-end as
  `tests/integration/test_simulation_experiment.py`.
- `benchmark/scenarios/simulation/` and
  `benchmark/reports/simulation/` — the implementation checklist's two
  recorded benchmarks: `SimulationRunRepository.get()`/`list()` latency
  (get ~0.08 µs, flat across 10³–10⁵ runs — the O(1) proof) and
  `SimulationStateCache` effectiveness (199/200 hit-rate, 98.8% of
  experiment wall time saved over a 10⁴-event history).

### Notes

- 100% statement coverage across all 22 `simulation` modules; full
  repository test suite (2580+ tests), `ruff`, and `mypy --strict`
  pass with zero findings.
- The six design spec §35 package acceptance proofs
  (no-fact-recomputation, no-statistics-reimplementation, immutability,
  interface-purity, no-architectural-drift, reproducibility) are each
  independently verified by dedicated tests.
- No architectural changes relative to the locked `v1.1.0` design —
  this is a pure implementation milestone. One disclosed spec-internal
  imprecision resolved minimally: §22's `by_category` resolves a run's
  category through the published-scenario store plus the model
  registry (the locked `SimulationRun` shape carries neither field),
  documented in `discovery.py`'s own module docstring.

## [1.7.0] - 2026-07-08

Digital Twin implementation milestone.

This release delivers the full production implementation of the
`mineproductivity.digital_twin` package against the architecture
approved in the `v1.0.0` milestone (Design Specification,
Implementation Checklist, and ADR-0008) — the platform's stateful
representation layer, built directly on `decision`, and the first
package in the series whose central abstraction is entity-shaped
(`core.BaseEntity[str]`) rather than stateless. The complete design
spec §6 module list (fifteen modules) ships in one implementation
phase.

### Added

- `Twin` (ABC) — a frozen `core.BaseEntity[str]` subclass by literal
  inheritance: identity-based equality inherited unchanged, `scope`
  frozen at provisioning time, state changes producing a new instance
  via `with_state()`, never in-place mutation — and `TwinContext`,
  carrying `KPIResult`/`AnalyticsResult`/`DecisionResult` evidence
  read, never re-derived.
- `TwinMetadata`/`TwinCategory` (closed eleven-member enum) and the
  eleven twin category base classes (`MineTwin` through
  `ProductionTwin`), each contributing only an import-time
  namespace/category-conformance check, mirroring `kpis`' nine
  category bases.
- `TwinStatus` — the instance-level operational lifecycle
  (`Provisioned`/`Synchronized`/`Stale`/`Degraded`/`Retired`);
  `Retired` is terminal and enforced by the synchronizer.
- `TwinState` (open, documented `attributes` mapping plus its own
  per-value `schema_version` — the third, independent versioning axis)
  and `TwinSnapshot` (point-in-time capture reusing `events.AsOf`,
  deliberately distinct from `events.EventSnapshot`).
- `TwinSynchronizer`/`SyncPolicy` — live synchronization via
  `events.EventBus.subscribe`, cold-start reconstruction via
  `events.EventStore.replay` (provably convergent with incremental
  synchronization), `Degraded`-on-repeated-failure lifecycle handling,
  and repository-mediated per-id state swaps; `TwinStateConflictError`
  raised only when a non-conforming repository violates the per-id
  write-serialization contract.
- `TelemetryReading` — the twin-local shape of already-event-sourced
  sensor readings; deliberately not a second ingestion boundary
  parallel to `connectors.FMSConnector`.
- `TwinSimulationModel` — an interface-only ABC with zero concrete
  subclasses by design (ADR-0008), the twin-state-level half of the
  bridge whose business-decision-level half is `decision.WhatIfEngine`;
  `TwinSimulationResult` defined ahead of any producer.
- `by_category`/`by_scope` — plain `core.PredicateSpecification`
  discovery factories composed with `TwinRepository.list()`.
- `TwinRepository` — a literal `type` alias over
  `core.BaseRepository[Twin, str]` (the strongest reuse in the series);
  the reference implementation is `core.InMemoryRepository`, unchanged,
  with zero new persistence code.
- `TwinStateCache` — evidence-input caching keyed by
  `(twin_id, as_of)`; never authoritative for current state
  (deliberately not a reuse of `kpis.ResultCache` — recorded
  "shape fits, coupling doesn't" trade-off).
- `TwinResult`/`SyncResult`/`TwinSimulationResult` result family and
  the full exception hierarchy (`TwinValidationError`,
  `TwinNotFoundError`, `TwinSyncError`, `TwinVersionConflictError`,
  `TwinStateConflictError`).
- `digital_twin.REGISTRY`/`register` — the Registry Framework
  specialization, exactly as `decision`/`analytics`/`kpis` specialize
  it; the package itself ships zero registered built-in twin types by
  design.
- `examples/digital_twin/` — four runnable, `mypy --strict`/`ruff`-clean
  example scripts per the implementation checklist: the design spec §15
  worked example end-to-end (cold-start + live subscribe), discovery
  composition, snapshot capture + serialization round-trip, and a
  third-party entry-point twin type.
- `benchmark/scenarios/digital_twin/` and
  `benchmark/reports/digital_twin/` — the implementation checklist's
  two recorded benchmarks: `TwinRepository.get()`/`list()` latency
  (get ~0.08 µs, flat across 10³–10⁵ twins — the O(1) proof) and
  cold-start replay cost vs. history length with/without
  `TwinSnapshot` seeding.

### Notes

- 100% statement coverage across all 16 `digital_twin` modules; full
  repository test suite (2380+ tests), `ruff`, and `mypy --strict` pass
  with zero findings.
- The seven design spec §32 package acceptance proofs
  (no-fact-recomputation, immutability, interface-purity,
  no-architectural-drift, replay-consistency, scope-immutability,
  repository-substitutability) are each independently verified by
  dedicated tests.
- No architectural changes relative to the locked `v1.0.0` design —
  this is a pure implementation milestone.

## [1.6.0] - 2026-07-08

Decision Intelligence implementation milestone.

This release delivers the full production implementation of the
`mineproductivity.decision` package against the architecture approved in
the `v0.9.0` milestone (Design Specification, Implementation Checklist,
and ADR-0007) — the platform's prescriptive layer, built directly on
`analytics`. Delivered across four internal phases (Foundation, Rule
Engine, Analysis Layer, Operational Services), all bundled into this one
release since none of the intermediate phases were independently
tagged.

### Added

- `DecisionModel` (ABC)/`DecisionContext`, `DecisionMetadata`/
  `DecisionCategory`, and the full `DecisionResult` result-model
  hierarchy (`Recommendation`, `RankedRecommendation`, `ActionPlan`,
  `Alert`, `RootCauseResult`, `WhatIfResult`, plus supporting value
  objects) (Foundation).
- `DecisionPipeline`/`PipelineStage`/`ModelStage`, `Threshold`, and
  `decision.REGISTRY`/`register`, specializing the Registry Framework
  mechanism exactly as `analytics._registry`/`kpis._registry` do
  (Foundation).
- `Rule`/`RuleEngine`/`RuleEngineStage`, `DecisionStatus`/`Policy`
  (versioned publish/supersede governance), and `DecisionStrategy`
  (ABC)/`ThresholdDecisionStrategy` — the default, concrete,
  rule/threshold-driven strategy, self-registering into `REGISTRY`
  (Rule Engine).
- `DecisionScorer`/`ConfidenceScorer`, `RankingStrategy`
  (ABC)/`WeightedScoreRanking`, `ExplanationBuilder`/`ExplanationStage`,
  `ActionPrioritizer`, and the interface-only `RootCauseAnalyzer` with
  zero concrete subclasses by design (Analysis Layer).
- `WhatIfEngine` — an interface-only extension point with zero concrete
  subclasses by design, reusing `events.AsOf`'s reserved `scenario`
  field (Operational Services).
- `ActionPlanner` — dependency-respecting topological action ordering
  via its own narrow, self-contained implementation (deliberately not
  `kpis.DependencyGraph`) (Operational Services).
- `AlertGenerator` — produces an `Alert` from a `ThresholdBreach` or a
  high-severity `Recommendation` (Operational Services).
- `RealTimeDecisionSession`/`BatchDecisionRunner` — the two execution
  modes, composing `kpis.KPIEngine`/`analytics.BatchAnalyticsRunner`
  rather than recomputing anything themselves (Operational Services).
- `DecisionAuditTrail`/`DecisionAuditEntry` — the append-only
  accountability record every operationally-actionable
  `DecisionPipeline` run can feed (Operational Services).
- `recommendation.py` — the design spec §6 generation-logic module,
  with no public API of its own per §6's own entry for it
  (`ThresholdDecisionStrategy` delegates `Recommendation` construction
  to it); originally folded into `strategy.py`, extracted in this
  release's completion pass so the package structure matches §6's
  twenty-two-module list exactly (completion pass).
- `examples/decision/` — four runnable, `mypy --strict`/`ruff`-clean
  example scripts per the implementation checklist: the design spec §9
  worked example end-to-end over real `UTIL.OEE`/trend evidence,
  action prioritization + dependency-respecting planning, a
  `RealTimeDecisionSession` over a live `EventBus`, and a
  third-party-style entry-point plugin strategy (completion pass).
- `benchmark/scenarios/decision/` and `benchmark/reports/decision/` —
  the implementation checklist's two recorded benchmarks:
  `RuleEngine.evaluate()` throughput (~1.3–1.6 M rules/s, flat across
  10–250-rule batches) and `DecisionAuditTrail` append/query latency
  (append ~0.3 µs/entry, flat across 10³–10⁵ entries — the O(1) proof)
  (completion pass).
- Checklist acceptance-proof tests added to the suite: real-time/batch
  parity (`RealTimeDecisionSession.latest()` vs. `BatchDecisionRunner`
  over the same assembled context), `DecisionAuditTrail.query()`
  non-blocking under concurrent `record()` calls, and
  registered-by-default coverage for the two built-in strategies
  (completion pass).
- Design spec §12's activation gate: `policy.publish_policy` now raises
  `DecisionModelNotFoundError` when a `Policy` is published as `Active`
  while its `strategy_code` names no registered `DecisionModel` —
  failing at activation time, never silently at first evaluation; a
  `Proposed` policy may still be authored ahead of its strategy's
  registration (completion pass).

### Notes

- 100% statement coverage across all 23 `decision` modules; full
  repository test suite (2160+ tests), `ruff`, and `mypy --strict` pass
  with zero findings.
- `decision` is now feature-complete per the Reference Implementation
  Blueprint's design spec §6 module list — the only remaining future
  work is a concrete `RootCauseAnalyzer`/`WhatIfEngine` plugin (neither
  is expected to ship inside this package itself, by design) and
  whatever `digital_twin`/`simulation`/`optimization`/`agents`/
  `visualization` need from this package as those packages move from
  architecture-complete to implemented.
- No architectural changes relative to the locked `v0.9.0` design — this
  is a pure implementation milestone.

## [1.5.0] - 2026-07-07

Analytics Engine implementation milestone.

This release delivers the full production implementation of the
`mineproductivity.analytics` package against the architecture approved in
the `v0.8.0` milestone (Design Specification, Implementation Checklist, and
ADR-0006) — the platform's statistical and analytical computation layer,
built directly on `kpis`.

### Added

- `AnalyticsModel` (ABC)/`AnalyticsContext`, `AnalyticsMetadata`/
  `AnalyticsCategory`, and the full `AnalyticsResult` result-model
  hierarchy (Foundation).
- `AnalyticsPipeline`/`PipelineStage`/`ModelStage` and `AggregationEngine`/
  `GroupBySpec` (Metric Pipelines & Aggregation), including
  `AggregationEngine.reduce()`.
- `describe`, `percentile`, `histogram`, `distribution`,
  `confidence_interval` (Statistical Primitives), and
  `rolling_mean`/`rolling_std`/`rolling_apply` (Rolling Analytics).
- `TrendModel`/`LinearTrendModel`, `BaselineModel`/`RollingBaselineModel`,
  `BenchmarkModel`/`BandBenchmarkModel` — each self-registering into the
  new `analytics.REGISTRY`.
- `DataQualityScorer`/`MissingDataPolicy`/`DataQualityStage` (Data Quality
  & Missing Data Handling).
- `ForecastingModel`, `AnomalyDetector`, `OutlierDetector` — interface-only
  extension points with zero concrete subclasses by design (ADR-0006).
- `BatchAnalyticsRunner`, `StreamingAnalyticsSession`,
  `IncrementalAccumulator` (Execution Modes), the latter implementing
  Welford's online algorithm for O(1) streaming mean/variance.
- `analytics.REGISTRY`/`register` (`_registry.py`), specializing the
  Registry Framework mechanism exactly as `kpis._registry` does.

### Notes

- 100% statement coverage across all 22 `analytics` modules; full repository
  test suite, `ruff`, and `mypy --strict` pass with zero findings.
- No architectural changes relative to the locked `v0.8.0` design — this is
  a pure implementation milestone.

## [1.4.0] - 2026-07-06

Visualization Architecture milestone.

This release completes the architectural design of the Visualization
subsystem — the seventh package built on top of the Foundation Layer and
the final package in the platform's architecture, sitting directly above
the now-locked `agents`. No production implementation is included; this
release delivers the approved architecture specification, implementation
checklist, and architectural decision record that will guide future
development.

### Added

- Visualization Design Specification.
- Visualization Implementation Checklist.
- ADR-0012: Visualization Architecture Decision Record.
- Repository-wide version bump to v1.4.0 reflecting the current release.

### Notes

- This is an architecture milestone only.
- No production Visualization implementation is included.
- Two interface-only ABCs (`Visualization`, `Renderer`) are defined with
  zero concrete implementations, mirroring the same discipline already
  applied by every prior Intelligence-tier milestone.
- This is the final package in the platform's architecture; no future
  package is anticipated above it.

## [1.3.0] - 2026-07-05

AI Agents Architecture milestone.

This release completes the architectural design of the AI Agents
subsystem — the sixth package built on top of the Foundation Layer,
sitting directly above the now-locked `optimization`. No production
implementation is included; this release delivers the approved
architecture specification, implementation checklist, and architectural
decision record that will guide future development.

### Added

- AI Agents Design Specification.
- AI Agents Implementation Checklist.
- ADR-0011: AI Agents Architecture Decision Record.
- Repository-wide version bump to v1.3.0 reflecting the current release.

### Notes

- This is an architecture milestone only.
- No production AI Agents implementation is included.
- Three interface-only ABCs (`Agent`, `Tool`, `AgentMemory`) are defined
  with zero concrete implementations, mirroring the same discipline
  already applied by every prior Intelligence-tier milestone.
- Forms the architectural foundation for the future Visualization
  milestone.

## [1.2.0] - 2026-07-05

Optimization Architecture milestone.

This release completes the architectural design of the Optimization
subsystem — the fifth package built on top of the Foundation Layer,
sitting directly above the now-locked `simulation`. No production
implementation is included; this release delivers the approved
architecture specification, implementation checklist, and architectural
decision record that will guide future development.

### Added

- Optimization Design Specification.
- Optimization Implementation Checklist.
- ADR-0010: Optimization Architecture Decision Record.
- Repository-wide version bump to v1.2.0 reflecting the current release.

### Notes

- This is an architecture milestone only.
- No production Optimization implementation is included.
- Six interface-only ABCs (`LinearProgrammingModel`,
  `MixedIntegerProgrammingModel`, `ConstraintProgrammingModel`,
  `MultiObjectiveModel`, `EvolutionaryMetaheuristicModel`,
  `NetworkOptimizationModel`) are defined with zero concrete
  implementations, mirroring the same discipline already applied by every
  prior Intelligence-tier milestone.
- Forms the architectural foundation for the future AI Agents and
  Visualization milestones.

## [1.1.0] - 2026-07-05

Simulation Architecture milestone.

This release completes the architectural design of the Simulation
subsystem — the fourth package built on top of the Foundation Layer,
sitting directly above the now-locked `digital_twin`. No production
implementation is included; this release delivers the approved
architecture specification, implementation checklist, and architectural
decision record that will guide future development.

### Added

- Simulation Design Specification.
- Simulation Implementation Checklist.
- ADR-0009: Simulation Architecture Decision Record.
- Repository-wide version bump to v1.1.0 reflecting the current release.

### Fixed

- `tests/unit/core/test_public_api.py::TestPackageVersion` compared
  `mineproductivity.__version__` against a hardcoded string literal,
  requiring an edit on every version bump. Rewritten to compare against
  `importlib.metadata.version("mineproductivity")` — the installed
  package's own metadata — so the test remains correct across future
  releases with no changes required.

### Notes

- This is an architecture milestone only.
- No production Simulation implementation is included.
- Four interface-only ABCs (`MonteCarloModel`, `DiscreteEventModel`,
  `SystemDynamicsModel`, `CalibrationModel`) are defined with zero
  concrete implementations, mirroring the same discipline already
  applied by the Analytics, Decision Intelligence, and Digital Twin
  milestones.
- Forms the architectural foundation for the future Optimization,
  AI Agents, and Visualization milestones.

## [1.0.0] - 2026-07-05

Digital Twin Architecture milestone.

This release completes the architectural design of the Digital Twin
subsystem. No production implementation is included; this release delivers
the approved architecture specification, implementation checklist, and
architectural decision record that will guide future development.

### Added

- Digital Twin Design Specification.
- Digital Twin Implementation Checklist.
- ADR-0008: Digital Twin Architecture Decision Record.
- Repository-wide version bump to v1.0.0 reflecting the current release.

### Notes

- This is an architecture milestone only.
- No production Digital Twin implementation is included.
- Forms the architectural foundation for the future Simulation,
  Optimization, AI Agents, and Visualization milestones.

## [0.9.0] - 2026-07-04

Decision Intelligence Architecture milestone.

This release completes the architectural design of the Decision Intelligence
subsystem. No production implementation is included; this release delivers the
approved architecture, implementation roadmap, and architectural decision
records that will guide future development.

### Added

- Decision Intelligence Design Specification.
- Decision Intelligence Implementation Checklist.
- ADR-0007: Decision Intelligence Architecture Decision Record.
- Documentation updates reflecting the v0.9.0 architecture milestone.
- README updated with architecture progress, project status, badges, and
  current release information.
- Citation metadata updated to use the Zenodo Concept DOI.

### Fixed

- Corrected broken documentation links in ADR-0007.
- Documentation validation passes with zero broken links.
- README and citation information synchronized with the latest architecture
  milestone.

### Notes

- This is an architecture milestone only.
- No production Decision Intelligence implementation is included.
- The next planned milestone is **v1.0.0 – Digital Twin Architecture**.

### Added

- Nothing yet.

## [0.8.0] - 2026-07-04

Analytics Engine Architecture milestone.

This release completes the architectural design of the Analytics Engine. No
production implementation is included; this release provides the approved
architecture specification, implementation checklist, and ADR defining the
Analytics subsystem.

### Added

- Analytics Engine Design Specification.
- Analytics Engine Implementation Checklist.
- ADR-0006: Analytics Engine Architecture Decision Record.
- Architecture documentation for the Analytics subsystem.

### Notes

- Architecture milestone only.
- No production Analytics Engine implementation is included.
- Forms the architectural foundation for the Decision Intelligence milestone.

## [0.7.4] - 2026-07-03

Production Readiness Validation — a first-time-user onboarding audit with
no new functionality. Every installation method, the "verify the install"
snippet, and every runnable example and notebook were followed exactly as
documented, in fresh environments, from a genuinely fresh clone of what is
now the actual published `main` branch.

### Added

- `examples/quickstart/01_five_minute_tour.py`: the five-minute tour —
  one truck (`ontology`), one shift, two haul cycles, and one KPI
  (`PROD.TPH`) read straight off the Standard Library, in ~50 lines.
  `examples/quickstart/` was, despite its own README's stated purpose
  ("mirroring `notebooks/beginner/` in code form"), still an empty
  placeholder even though every subsystem it needs has been implemented
  since v0.7.0.
- A "Next Steps" section in the root `README.md`, immediately after the
  install-verification snippet: a table routing a first-time user to
  the quickstart script, the beginner notebook, and the right first
  example for KPIs, ontology, connectors, events, and the registry/
  plugin discovery mechanism - none of which the README linked to
  anywhere before this release, despite all of it existing and being
  exercised in CI.
- Anchor-fragment validation in `scripts/quality/check_docs.py`:
  previously only checked that a link's *file* resolves, not that its
  `#anchor` is an actual heading in the target file. This caught a real
  bug on first run (see Fixed).

### Fixed

- The root `README.md`'s "Architectural Layering & Dependency Direction"
  section linked to `docs/architecture/README.md#dependency-rules`, an
  anchor that has never existed in that file (the closest real heading
  is `#dependencies`, a different section entirely). The surrounding
  sentence was also stale - it read "documented (not yet mechanically
  enforced)," which stopped being true as of the Ontology milestone
  (v0.4.0): every implemented package's own `test_public_api.py::
  TestNoForbiddenDependencies` has enforced this mechanically ever
  since. Rewritten to state the (now true) mechanical enforcement and
  link to a package README section that actually exists
  (`src/mineproductivity/kpis/README.md#dependency-rules`).

### Notes

- All four installation methods (`pip install git+https://...`,
  `pip install .` from a local checkout, `pip install -e ".[dev]"`,
  and the wheel built by `python -m build`) were re-verified against
  the actual current `main` branch (not a stale local copy) in fresh
  virtual environments, and produced byte-for-byte the output the
  README documents.
- All 21 example scripts across `quickstart/`, `core/`, `events/`,
  `ontology/`, `registry/`, `connectors/`, and `kpis/`, plus
  `notebooks/beginner/01_first_kpi_lookup.ipynb`, were re-executed
  fresh and pass.
- `docs/developer_guide/` (the in-repo home for the locked Developer &
  Cookbook Guide's three parts) remains an unpopulated placeholder -
  not fixed in this release. Recreating a multi-part external reference
  document from scratch is content authorship, not an onboarding-
  friction fix, and risks drifting from the actual locked source
  material. The new "Next Steps" section in `README.md` says so
  explicitly rather than leaving a first-time user to discover the gap
  by clicking through to an empty page.
- No architecture, dependency direction, or public API changed. No new
  packages were added.

## [0.7.3] - 2026-07-03

CI/CD & Cross-Platform Validation — a release-engineering milestone with no
new functionality. The three placeholder GitHub Actions workflows left over
from the repository-skeleton phase (`ci.yml`, `docs.yml`, `release.yml`,
each literally titled "Placeholder... no implementation yet") are replaced
with a real, enterprise-grade pipeline.

### Added

- `.github/workflows/ci.yml`: the correctness gate. `pytest` + coverage
  (`--cov-fail-under=95`) across a `{ubuntu, windows, macos} x {3.12,
  3.13}` matrix (the two Python versions `pyproject.toml` actually
  declares support for), plus Python 3.10/3.11 on Ubuntu as non-blocking
  early signal. Builds the wheel and sdist, `twine check --strict`s
  them, then validates wheel installs across all three OSes and
  sdist/editable/GitHub installs (at the exact commit under test) in
  fresh environments, each followed by a real smoke test.
- `.github/workflows/quality.yml`: the cleanliness gate. `ruff check` +
  `ruff format --check`, `mypy --strict`, documentation validation
  (every relative Markdown link in the repository, every fenced
  ```python``` block in the root and package READMEs), and full
  notebook execution.
- `.github/workflows/benchmark.yml`: a performance *smoke* test -
  generous wall-clock ceilings on cold-import time, a batched KPI
  compute, and dependency-graph resolution, meant to catch a
  catastrophic regression, not track performance over time.
- `.github/workflows/dependency-review.yml`, `codeql.yml`,
  `security.yml`: PR-triggered dependency vulnerability/license review,
  weekly CodeQL static analysis, and weekly + `pyproject.toml`-triggered
  `pip-audit` against every installed dependency.
- `.github/workflows/release.yml`: on a `v*.*.*` tag push, builds and
  `twine check`s the wheel/sdist, verifies the tag matches
  `mineproductivity.__version__` (failing the release if they
  disagree), and creates a GitHub Release with both artifacts attached.
  Does **not** publish to PyPI — a fully commented-out Trusted
  Publishing (OIDC) job is included, ready to enable once a PyPI
  Trusted Publisher is registered for this repository.
- `scripts/quality/smoke_test.py`, `check_docs.py`, `perf_smoke.py`:
  the reusable scripts the workflows above call, each also runnable
  standalone by a contributor.
- `docs/governance/CI_CD_GUIDE.md`: workflows, branch strategy (trunk
  -based off `main`), release flow, developer workflow, and a
  failure-handling runbook per workflow.
- Two new README badges (`CI`, `Quality`) linking to the new workflows'
  live status. No coverage-percentage badge added — that needs a
  reporting service (Codecov/Coveralls) this milestone deliberately
  does not wire up (see `docs/governance/CI_CD_GUIDE.md`'s Future Work).

### Fixed

- `.github/CODEOWNERS` only listed `core`, `ontology`, and `events` —
  missing `registry`, `plugins`, `connectors`, and `kpis` entirely,
  each implemented and released since the file was last touched.
- `scripts/quality/check_docs.py` (documentation snippet validation)
  root-caused a genuine `dataclasses` gotcha rather than working around
  it: every source file in this codebase uses `from __future__ import
  annotations`, so a snippet's `ClassVar[str]` field annotation is a
  *string* at class-definition time, and `dataclasses` resolves such
  strings via `sys.modules[cls.__module__].__dict__`. Executing a
  snippet with `__module__ == "__main__"` therefore resolved against
  the *checker script's own* globals (which never import `ClassVar`),
  silently misclassifying every `ClassVar` field as a plain field with
  a default and breaking dataclass field ordering for reasons that had
  nothing to do with the documentation being checked. Fixed by
  registering each checked file's namespace as its own uniquely-named
  fake module in `sys.modules` for the duration of the check.

### Notes

- `pyproject.toml`'s `events` extra pins `pyarrow>=14,<19`, which
  permits a real, known Use-After-Free (`PYSEC-2026-113`, fixed in
  `pyarrow>=23.0.1`). `security.yml` records this as a deliberate,
  documented exception (`--ignore-vuln`) rather than a silently-ignored
  finding or a permanently-red gate: fixing it properly means bumping
  across roughly nine major `pyarrow` releases and re-validating
  `events`' `ArrowEventCodec`/`ParquetEventCodec` against the new API -
  a framework-compatibility change out of scope for CI/CD tooling work.
  See `docs/governance/CI_CD_GUIDE.md`'s Known Exceptions.
- `docs.yml` builds with `mkdocs build`, not `--strict`:
  `docs/architecture/*.md` (the locked design specifications)
  legitimately cross-link to the root `README.md` and to package
  READMEs under `src/mineproductivity/`, both outside mkdocs' own
  `docs_dir` — correct for GitHub's file browser, unresolvable within a
  single mkdocs site build, and unrelated to whether the site itself is
  sound.
- No architecture, dependency direction, or public API changed. No new
  packages were added. PyPI publishing remains intentionally disabled.

## [0.7.2] - 2026-07-03

Documentation & API Validation - a documentation-and-API-quality audit with
no new functionality. Every README, example, notebook, and documented code
snippet across the repository was executed or cross-checked against the
real, current source; the public API surface of all seven implemented
packages was re-verified for intentional, sorted, gap-free `__all__` lists.

### Fixed

- `registry.registered_in()`'s docstring (and its module docstring) claimed
  `kpis.register` and `ontology.register_equipment` are "thin,
  partially-applied" wrappers around it. Neither is: `ontology` sits below
  `registry` in the dependency stack and cannot import it at all (its
  entity-type registry is a separate, internal mechanism that predates
  `registry`); `kpis.register` hand-rolls its own decorator to also raise
  `KPICircularDependencyError` at registration time. Only
  `connectors.register_connector` is genuinely built from this function.
  Corrected in both the docstring and `registry/README.md`'s matching
  Extension Guide example, which is rewritten to use the accurate
  `connectors` example instead.
- Two package-README "recipe" code snippets meant to be copy-paste starting
  points (`events/README.md`'s `BlastEvent` example,
  `ontology/README.md`'s `UndergroundJumbo` example) were missing the
  imports (`dataclass`, `field`, `ClassVar`, and the relevant base classes)
  a reader would actually need to run them.
- `examples/README.md` still listed only the unimplemented placeholder
  example directories (`quickstart/`, `production/`, `visualization/`,
  `ai/`, `digital_twin/`) and said "Dependencies: mineproductivity (once
  implemented)" — omitting the six implemented, runnable example
  directories (`core/`, `events/`, `ontology/`, `registry/`, `connectors/`,
  `kpis/`, 20 scripts total) entirely. Rewritten to list both groups
  accurately.
- `docs/api/README.md` said "Placeholder - no API exists yet to document,"
  no longer true with seven implemented, documented packages; corrected to
  point at each package's own `README.md` while automated reference
  generation remains genuinely not wired up.
- `docs/architecture/README.md` described the five now-fully-implemented
  design specifications as packages that merely "will depend on `core`,"
  future tense left over from before any of them existed.
- `tests/unit/kpis/README.md` still read "Placeholder — no implementation
  exists yet in the corresponding source package" despite the real,
  344-test, 100%-coverage suite the KPI Engine milestone added — the one
  package README this repository's "update the test README alongside the
  test suite" convention was missed for. Rewritten to match the pattern
  already used by the other six implemented packages' test READMEs.

### Notes

- Every fenced ```python block in the root `README.md` and all seven
  implemented package READMEs was extracted and executed; every runnable
  example under `examples/` (20 scripts) and the one existing notebook
  (`notebooks/beginner/01_first_kpi_lookup.ipynb`) were executed end to
  end with zero failures.
- Zero broken relative links found across all 130 Markdown files in the
  repository.
- Exception hierarchies, `BaseMetadata` subclassing, and `Protocol` naming
  were reviewed across all seven implemented packages for cross-package
  consistency; no inconsistency was found serious enough to warrant an API
  change (none was made — none is in scope for this milestone).
- No architecture, dependency direction, or public API changed. No new
  packages were added. `docs/architecture/*_Design_Specification.md`'s own
  "Design specification only - no implementation" status lines are now
  stale for the five implemented frameworks but were deliberately left
  unmodified as locked governance documents, out of scope for this
  milestone.

## [0.7.1] - 2026-07-03

Packaging & Installation Validation - a release-engineering milestone with
no new functionality. `mineproductivity` was built, checked, and installed
from every supported distribution channel: wheel, sdist, `pip install -e .`,
and `pip install git+https://github.com/imanojkumar/MineProductivity.git`.

### Fixed

- `pyproject.toml` declared a `[project.scripts]` console entry point
  (`mineproductivity = "mineproductivity.cli:main"`) pointing at a
  `main()` function that has never existed - `mineproductivity.cli` is
  still an unimplemented structural placeholder. Every `pip install`
  therefore shipped a console script that crashed
  (`ImportError: cannot import name 'main' from 'mineproductivity.cli'`)
  the moment it was run. The entry point is removed until a real CLI
  exists; nothing else in `[project.scripts]` is affected since it was
  the only entry.

### Changed

- `pyproject.toml` gained a `keywords` field (`mining`, `productivity`,
  `kpi`, `digital-twin`, `ontology`, `event-sourcing`, `python`),
  matching `CITATION.cff`'s existing keyword list - previously absent,
  hurting PyPI/GitHub topic discoverability.
- `README.md`'s "Getting Started" section, which still read "There is
  no functionality to run yet" (a leftover from the `v0.1.0` skeleton
  phase), is rewritten with accurate, verified installation instructions
  (GitHub install, local install, the optional dependency groups table,
  and a working install-verification snippet) ahead of the existing
  contributor development-setup instructions.

### Notes

- `python -m build` produces a clean wheel and sdist; `twine check`
  passes both with no warnings.
- The wheel (`py3-none-any`, zero third-party dependencies) was
  installed into a clean virtual environment and exercised: every
  top-level subpackage (`core`, `events`, `ontology`, `registry`,
  `connectors`, `kpis`, `plugins`) imports cleanly with no optional
  extras installed, and a real `PROD.TPH` computation was run
  end-to-end against `REGISTRY`.
- The sdist, a fresh GitHub install (`pip install git+...`), and
  `pip install -e .` were each independently verified the same way, in
  their own clean virtual environments; `pip install -e ".[analytics]"`
  additionally re-ran eight representative examples (one per
  implemented package plus all four `examples/kpis/` scripts), all
  exiting `0`.
- No dependency direction, public API, or architecture changed. No new
  packages were added.

## [0.7.0] - 2026-07-03

### Added

- `mineproductivity.kpis`: the KPI Engine — the platform's most
  important package, making every performance indicator a discoverable,
  versioned, self-describing object ("KPI-as-object") rather than a
  formula buried in a script, implementing
  `docs/architecture/05_KPI_Engine_Design_Specification.md` exactly.
  `KPIMetadata` (the full 29-field governed Standard Library schema),
  `BaseKPI`/`CompositeKPI` (leaf vs. composite, never conflated),
  nine category base classes (`ProductionKPI`, `UtilizationKPI`,
  `MaintenanceKPI`, `HaulageKPI`, `DelayKPI`, `EnergyKPI`, `QualityKPI`,
  `CostKPI`, `SafetyKPI`), `KPIEngine` (orchestration only - zero
  metric-specific logic, AD-KP-01), `DependencyGraph`
  (`topological_order`/`detect_cycle`, cycle detection proven at
  registration time, never deferred to first execution),
  `aggregation.combine_results` (structurally enforcing the
  RATIO-never-averaged rule), `Window`/`RollingWindow`/
  `CumulativeWindow`, `ResultCache` (thread-safe,
  `(code, window, scope, fingerprint)`-keyed), `specialize()` (KPI
  inheritance, e.g. `PROD.TPH.Ore`), `parse_identifier`/`KPIIdentifier`
  (the `NAMESPACE.Name` naming standard), `KPIValidator`, and
  `CertificationFixture`/`run_certification_fixture`.
- Four pluggable `ExecutionBackend` implementations - `PandasBackend`
  (default), `NumPyBackend` (no DataFrame dependency at all),
  `PolarsBackend`, and `DuckDBBackend` — with mechanically proven
  backend parity: the same `_compute` produces an identical
  `KPIResult.value` regardless of which backend assembled its rows.
- A 12-KPI Standard Library reference implementation: `PROD.TPH`,
  `UTIL.PA`/`UTIL.UA`/`UTIL.Performance`/`UTIL.OEE` (the last a
  composite worked example built on the other three), `MAINT.MTTR`,
  `HAUL.TruckCycleTime`, `DISP.TotalDelayHours`, `ENERGY.FuelConsumed`,
  `QUAL.OreProportion`, `COST.FuelPerTonne` (a cross-event-type
  computation over `CONSUMPTION` and `CYCLE` rows), and
  `SAFE.SpeedViolationCount`.
- `tests/unit/kpis/`: a full unit test suite (344 tests, 100% line
  coverage) mirroring `src/mineproductivity/kpis/` 1:1, including
  backend parity tests, a dedicated regression proof of the Cookbook
  Part I Ch. 6 ratio-correctness worked numbers (A-shift 1,300 t/h over
  12h + B-shift 1,100 t/h over 6h combine to 1,233.3 t/h, never the
  naive 1,200 average), and a `ResultCache` concurrency stress test.
- `tests/fixtures/kpis/` and `tests/integration/test_kpi_pipeline.py`:
  a realistic one-shift golden dataset (every canonical event type) and
  the full CSV → canonical events → `EventStore` → `KPIEngine` pipeline
  proven end to end with no stage bypassed.
- `examples/kpis/`: four runnable examples - single-KPI execution,
  composite `UTIL.OEE` execution, batched multi-KPI `summary()`, and
  `REGISTRY` discovery - plus a shared sample-dataset loader.
- `notebooks/beginner/01_first_kpi_lookup.ipynb`: the first notebook in
  the Learning & Benchmark Suite v1.0's pedagogical progression, proven
  to execute headlessly end to end.
- `kpis/README.md`: architecture, dependency rules, public API
  reference, extension guide, design rationale, and anti-patterns.
- New optional dependency group `notebooks` (`jupyter`, `ipykernel`).

### Fixed

- `DuckDBBackend.group_and_aggregate` was silently dropping the
  group-by column from its projected output (`relation.aggregate()`
  only returns what is listed in its own SELECT expression) - a
  genuine backend-parity violation, caught by the pre-pytest smoke
  test and now covered by a dedicated regression test.
- `PhysicalAvailability._compute` (`UTIL.PA`) indexed `rows[0]`
  unconditionally, raising `IndexError` for a shift with genuinely zero
  `MaintenanceEvent` rows instead of returning `None`.
- `kpis/__init__.py`'s `__all__` was not actually alphabetically
  sorted (`REGISTRY` sat first rather than in its correct position).

### Notes

- `kpis` depends on `core`, `ontology`, `events`, and `registry`
  only — mechanically verified
  (`tests/unit/kpis/test_public_api.py`) to import nothing from
  `connectors`, `analytics`, `optimization`, `simulation`, `decision`,
  `digital_twin`, or `agents` - the single most load-bearing rule in
  the design specification.
- `KPIValidator`'s canonical time-model textual check now scopes to
  leaf (non-composite) `UtilizationKPI` subclasses only, since a
  composite's own formula composes other KPI codes' results rather than
  raw hour fields directly.
- `pyproject.toml` gained the `analytics` optional dependency group
  (`numpy`, `pandas`, `polars`, `duckdb`) and a `[[tool.mypy.overrides]]`
  entry for `pandas`/`polars`/`duckdb` (no bundled type stubs).

## [0.6.0] - 2026-07-03

### Added

- `mineproductivity.connectors`: the Connector Framework - the single,
  small contract every data source must satisfy to feed the platform,
  and the only place in the codebase permitted to know that a specific
  vendor or file format exists, implementing
  `docs/architecture/04_Connector_Framework_Design_Specification.md`
  exactly. `FMSConnector` (only `get_cycle_data`/`get_delay_data`
  abstract; four more `get_*_data` methods with no-op defaults) and
  `IngestionMode`; `Normalizer`/`FieldMapper`/`ReasonCodeMap` (the
  vendor-dialect-to-canonical translation layer, independently
  unit-testable without a live connection); `AuthProvider`/`Credentials`
  and `RetryPolicy`/`BackoffStrategy`/`run_with_retry` (shared, generic
  network-connector plumbing, with a mandatory concurrent-safe
  `AuthProvider.refresh()` guarantee); `ConnectorHealth`/`HealthStatus`;
  and `run_fms_contract_suite` (the shared structural contract every
  connector, built-in or plugin, is expected to pass).
- Six reference connectors, all genuinely functional (not stubs):
  `CSVConnector`/`ExcelConnector` (file, with local-timezone
  normalization to UTC), `RestConnector`/`GraphQLConnector` (network,
  stdlib `urllib` only - paginate, 401-triggered auth refresh, retry/
  backoff on transient failures), and `KafkaConnector`/`MqttConnector`
  (streaming, via a pluggable message-source abstraction rather than a
  broker client library dependency). All six are registered into
  `CONNECTORS` by default.
- Five OEM adapter shapes - `MineStarConnector`, `DispatchConnector`,
  `WencoConnector`, `ModularConnector`, `HexagonConnector` — plus an
  illustrative `ReasonCodeMap` per vendor. Documentation-only: both
  `get_cycle_data`/`get_delay_data` raise `NotImplementedError`, and
  none is registered by default. No vendor SDK code exists in this
  repository or is implied by these classes (design spec AD-CN-03).
- `tests/fixtures/connectors/`: small, synthetic (not vendor-derived)
  CSV fixtures — golden, malformed (Category D), and local-timezone
  (Category F) variants.
- `tests/unit/connectors/`: a full unit test suite (241 tests, 100%
  line coverage), including `RestConnector`/`GraphQLConnector` tested
  against a real, local `http.server.HTTPServer` (genuine socket I/O,
  not a patched client).
- `tests/integration/test_connector_pipeline.py`: the full CSV →
  `CSVConnector` → `EventValidator` → `EventStore` → query pipeline,
  plus Certification Categories A (golden), C (edge cases), D
  (corrupted data), and F (timezone).
- `examples/connectors/`: runnable examples for end-to-end CSV
  ingestion and a REST connector's auth-refresh/retry-backoff behavior
  against a real local HTTP server.
- `connectors/README.md`: architecture, dependency rules, public API
  reference, extension guide, design rationale, and anti-patterns.
- New optional dependency group `connectors` (`openpyxl`, and `tzdata`
  on Windows only) - imported lazily, never required to `import
  mineproductivity.connectors`.

### Notes

- `connectors` depends on `core`, `ontology`, `events`, and `registry`
  only — mechanically verified
  (`tests/unit/connectors/test_public_api.py`) to import nothing from
  `kpis`, `analytics`, `optimization`, `simulation`, `decision`,
  `digital_twin`, or `agents` - the single most load-bearing rule in
  the design specification.
- `pyproject.toml` gained `[[tool.mypy.overrides]]` entries for
  `openpyxl` (no bundled type stubs) and the registry test fixture
  packages (installed without a `py.typed` marker).

## [0.5.0] - 2026-07-03

### Added

- `mineproductivity.registry`: the generic, type-safe registration
  mechanism every domain package specializes rather than reimplements,
  implementing `docs/architecture/03_Registry_Framework_Design_Specification.md`
  exactly. `Registry[TKey, TItem]` (register/lookup/get/list/
  metadata_for, add-only registration with duplicate-key rejection),
  `EntryPointSpec`/`EntryPointDiscovery` (scans `importlib.metadata`
  entry-points, isolating any single entry-point's import failure from
  the rest of the scan), `registered_in()` (the generic `@register`
  decorator factory), `VersionRange`/`VersionCompatibility`
  (stdlib-only, dependency-free version-range gating), and
  `DiscoveryCache` (scan-once-per-process memoization, safe under
  concurrent calls for the same spec).
- `mineproductivity.plugins`: the plugin lifecycle layer built on
  `registry` - `PluginManifest`/`PluginDependency`, `PluginState`
  (`DISCOVERED`/`VALIDATED`/`ACTIVE`/`FAILED`/`DEACTIVATED`),
  `PluginLifecycle` (the ABC) and `_DefaultPluginLifecycle` (the
  reference implementation, in the pattern of `events._InMemoryEventStore`),
  `PluginLoader` (aggregates every entry-point group one manifest
  declares), and `resolve_activation_order()` (topological-sort
  dependency resolution via Kahn's algorithm, detecting missing
  dependencies and cycles).
- `tests/fixtures/plugins/`: two real, independently pip-installable
  fixture plugin packages (`registry-fixture-healthy`,
  `registry-fixture-broken`) used to prove discovery and isolation
  end-to-end against actual installed package metadata, not mocks.
- `tests/unit/registry/` and `tests/unit/plugins/`: full unit test
  suites (127 tests combined, 100% line coverage), including a
  thread-based concurrency stress test for `DiscoveryCache` and a
  dedicated isolation test proving one `Failed` plugin never blocks
  another's path to `Active`.
- `tests/integration/test_registry_plugin_discovery.py`: discovery,
  isolation, and full manifest-to-activation proven against the real
  fixture packages, plus a zero-core-change proof.
- `examples/registry/`: runnable examples for the full register →
  discover → lookup cycle (against a real, on-disk plugin module) and
  side-by-side compatible/incompatible plugin activation.
- `registry/README.md` and `plugins/README.md`: architecture,
  dependency rules, public API reference, extension guide, design
  rationale, and anti-patterns.

### Notes

- `registry` depends on `core` only; `plugins` depends on `core` and
  `registry` only — both mechanically verified
  (`tests/unit/registry/test_public_api.py`,
  `tests/unit/plugins/test_public_api.py`) to import nothing from any
  domain package (`ontology`, `events`, `connectors`, `kpis`,
  `analytics`, `optimization`, `simulation`, `decision`,
  `digital_twin`, `agents`).
- `pyproject.toml` gained a `[[tool.mypy.overrides]]` entry for the two
  registry test fixture packages (installed without a `py.typed`
  marker, since they exist only to prove real-package discovery).

## [0.4.0] - 2026-07-03

### Added

- `mineproductivity.ontology`: the Ontology Framework — the typed,
  machine-readable model of the mining world, implementing
  `docs/architecture/02_Ontology_Framework_Design_Specification.md`
  exactly. `BaseEntityType`/`EntityTypeMetadata` (the entity-type root,
  with structural validation enforced at construction and JSON Schema
  export via `to_schema()`), `Relationship`/`RelationshipKind` (explicit,
  typed edges between entity ids), `OntologyValidator` (contextual,
  cross-entity referential validation - an unresolved reference is always
  a warning, never a raised exception), and
  `KnowledgeGraphProjection`/`GraphNode`/`GraphEdge` (the contract a
  future Knowledge Graph builder consumes).
- Ten sub-ontology families, each a leaf of `BaseEntityType`: **equipment**
  (`EquipmentType`/`OperationalState` root plus 12 leaf types —
  `RigidHaulTruck`, `ArticulatedHaulTruck`, `HydraulicShovel`,
  `WheelLoader`, `LHD`, `BlastholeDrill`, `Dozer`, `Grader`, `WaterTruck`,
  `Crusher`, `Conveyor`, `Mill`), **material** (`Commodity`,
  `MaterialType`), **location** (`Mine`, `Pit`, `Bench`, `Route`, `Zone`,
  `Level`, `Stope`, `Drive`), **organization** (`Fleet`, `Crew`,
  `Operator`, `BusinessUnit`, `Contractor`), **production** (`Shift`,
  `ShiftPattern`, `ShiftCalendar`), **maintenance** (`FailureMode`,
  `MaintenanceWorkOrder`), **cost** (`CostCenter`, `CostCategory`),
  **quality** (`GradeAttribute`, `QualitySpecification`), **safety**
  (`HazardZone`, `SpeedLimitMap`, `SafetyEventType`), and
  **environmental** (`EmissionFactor`, `MonitoringPoint`).
- `mineproductivity.ontology.SafetyEventType`: relocated from
  `mineproductivity.events.canonical.safety_event` to its permanent,
  governed home in `ontology.safety`, for the identical reason
  `DelayCategory` is owned by `ontology` and not `events` (a closed,
  governed taxonomy is domain reference data, not event structure -
  design spec AD-ON-03). `events.SafetyEvent.safety_event_type` now
  imports and consumes this enum rather than defining its own copy.
- `tests/unit/ontology/`: a full unit test suite (207 tests, 100% line
  coverage), mirroring all ten sub-ontology families plus the
  cross-cutting root modules (`entity_type`, `relationship`,
  `graph_projection`, `validation`, `exceptions`, `public_api`).
- `tests/integration/test_ontology_model.py`: a multi-family mine model
  (location, equipment, organization, production, cost, safety) wired
  together with `Relationship` edges, validated end-to-end with
  `OntologyValidator`, projected through a `KnowledgeGraphProjection`,
  and cross-checked against `events.DelayEvent`/`events.SafetyEvent` to
  confirm the two packages share reference-data identity rather than
  duplicating it.
- `examples/ontology/`: runnable examples for equipment modelling,
  structural modelling with relationship traversal, and contextual
  validation.
- `ontology/README.md`: architecture, dependency rules, public API
  reference, extension guide, design rationale, and anti-patterns.

### Changed

- `mineproductivity.events.canonical.safety_event.SafetyEvent
  .safety_event_type` is now typed against `mineproductivity.ontology
  .SafetyEventType` instead of a locally-defined enum of the same shape.
  `events.SafetyEventType` remains importable (re-exported through
  `events.canonical` and `events`, unchanged for existing callers) but is
  now the exact same object as `ontology.SafetyEventType`, not a
  duplicate.

### Fixed

- `core.BaseEntity` has no `__post_init__`/`validate()` hook of its own
  (no package built entity *types* on top of it before this one) -
  `BaseEntityType` adds that hook locally, mirroring
  `core.BaseValueObject`'s existing `_normalize()`/`validate()` pattern
  exactly, without modifying the locked `core` package.
- `Relationship.validate()` previously raised the bare
  `core.ValidationError` instead of the package-scoped
  `ontology.exceptions.RelationshipError` its own exception hierarchy
  defines for exactly this case - fixed for consistency with every other
  validation path in this package.

### Notes

- `ontology` depends on `core` only - mechanically verified
  (`tests/unit/ontology/test_public_api.py`) to import nothing from
  `events`, `registry`, `connectors`, `kpis`, `analytics`, `optimization`,
  `simulation`, `decision`, `digital_twin`, or `agents`.
- `events` now depends on two ontology reference taxonomies -
  `DelayCategory` and `SafetyEventType` - both closed, governed enums with
  no behavior beyond what the design specification defines; still no
  ontology entity types, registry, or services are consumed by `events`.

## [0.3.0] - 2026-07-03

### Added

- `mineproductivity.events`: the Event Framework - the immutable,
  append-only event model (Event Sourcing) every derived state in the
  platform is computed from, implementing
  `docs/architecture/01_Event_Framework_Design_Specification.md` exactly.
  `EventID` (ULID-backed, stdlib-only), `EventVersion`, `EventMetadata`,
  `EventEnvelope` (with the mandatory three-timestamp temporal model),
  `BaseEvent` and the six canonical event types (`CycleEvent`,
  `DelayEvent`, `MaintenanceEvent`, `ProductionEvent`, `ConsumptionEvent`,
  `SafetyEvent`), `EventSchema`, `EventValidator`/`ConfidenceScore`/
  `ValidationOutcome`, `EventStore`/`EventQuery`/`EventFilter` and a
  reference `_InMemoryEventStore`, `EventBus`/`Subscription` and a
  reference `_InMemoryEventBus`, `AsOf`/`ReplayHandle` (time-travel) and
  `EventSnapshot`, and three serialization codecs (`JSONEventCodec` with
  no extra dependency; `ArrowEventCodec`/`ParquetEventCodec` behind the
  new optional `events` extra).
- `mineproductivity.ontology.reference.DelayCategory`: the minimal shared
  contract (a closed six-value enum) published ahead of the full Ontology
  Framework milestone, per Documentation Governance Rule #005, because
  `events.DelayEvent` requires it. No other ontology concept exists yet.
- `tests/unit/events/`: a full unit test suite (229 tests, 100% line
  coverage), including dedicated property tests for idempotency and the
  replay/snapshot equivalence law.
- `tests/integration/test_events_pipeline.py`: the full ingest → validate
  → append → publish → query → replay → serialize pipeline, end to end.
- `examples/events/`: runnable examples for first-event construction,
  replay/time-travel, and corrections.
- `events/README.md`: architecture, dependency rules, public API
  reference, extension guide, design rationale, and anti-patterns.

### Fixed

- A `@dataclass(slots=True)` + inheritance + bare `super()` gotcha in
  `EventMetadata.validate()` (slotted dataclasses rebuild the class
  object, which breaks the implicit `__class__` cell a zero-arg `super()`
  relies on) - fixed with the explicit two-argument form, with a
  regression test guarding it.
- An Arrow/Parquet limitation where an all-empty `metadata.attributes`
  column across a batch produced a zero-child struct type that Parquet's
  writer cannot represent - fixed by JSON-string-encoding that one
  open-ended field for the Arrow/Parquet codecs specifically.

### Notes

- `events` depends on `core` and, minimally, `ontology.DelayCategory`
  only - mechanically verified (`tests/unit/events/test_public_api.py`)
  to import nothing from `connectors`, `kpis`, `analytics`,
  `optimization`, `simulation`, `decision`, `digital_twin`, or `agents`.
- `pyproject.toml` gained an `events` optional-dependency group
  (`pyarrow`) and a `[[tool.mypy.overrides]]` entry for it (`pyarrow`
  ships no type stubs); the base install remains dependency-free.

## [0.2.0] - 2026-07-02

### Added

- `mineproductivity.core`: the platform's first implemented package,
  providing framework-agnostic, domain-agnostic foundational primitives —
  `BaseEntity`, `BaseValueObject`, `BaseIdentifier`/`UUIDIdentifier`,
  `BaseMetadata`, `BaseVersionedObject`, `BaseSpecification` (with
  `&`/`|`/`~` composition), `BaseRepository`/`InMemoryRepository`,
  `BaseFactory`, `BaseBuilder`, `BaseService`, `BaseValidator`/
  `ValidationResult`/`CompositeValidator`, `BaseSerializer`/
  `DataclassSerializer`, `BaseConfiguration`, `Result[T]`, `Maybe[T]`, the
  `MineProductivityError` exception hierarchy, and shared typing
  primitives (`Comparable`, `Identifiable`, `JSONValue`).
- `tests/unit/core/`: a full unit test suite for every `core` module
  (equality, hashing, immutability, validation, serialization, generics,
  ABC enforcement, edge cases).
- `examples/core/`: runnable examples demonstrating entities, value
  objects, repositories, factories, builders, validation, and
  serialization.
- `core/README.md`: architecture, dependency rules, public API reference,
  extension guide, design rationale, and anti-patterns for the package.

### Notes

- `core` has zero dependencies on any other `mineproductivity` package and
  zero knowledge of the mining domain (no KPI, event, ontology, equipment,
  dispatch, connector, analytics, optimization, digital twin, or decision
  concepts). Every other subsystem package remains an unimplemented
  structural placeholder.

## [0.1.0] - 2026-07-01

### Added

- Initial repository skeleton: full directory hierarchy for `src/`, `tests/`,
  `docs/`, `datasets/`, `notebooks/`, `examples/`, `benchmark/`,
  `certification/`, and `scripts/`, mirroring the locked Master Architecture
  Handbook v1.0 and Reference Implementation Blueprint v1.0.
- Packaging metadata (`pyproject.toml`) targeting Python 3.12+, using
  Hatchling and the `src/` layout.
- Governance and community files: `README.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `ROADMAP.md`, `CITATION.cff`.
- GitHub configuration: issue templates, pull request template, `CODEOWNERS`,
  and placeholder CI workflows (no CI logic implemented yet).
- Placeholder `README.md` files describing purpose, scope, responsibilities,
  contents, dependencies, future work, and references for every package and
  directory in the tree.

### Notes

- Zero business logic. No KPI calculations, digital twin implementation,
  connectors, AI agents, analytics, optimization, or event processing exist
  in this release.
