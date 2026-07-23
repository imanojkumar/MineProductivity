# Learning Suite - Progress Tracker

> **Live execution state.** The stable plan is
> [`LEARNING_ROADMAP.md`](LEARNING_ROADMAP.md) (locked); this file is the
> authoritative record of *what is actually done*, verified against the
> repository. Update it at the end of every session.

**Last updated:** 2026-07-18
**Active milestone:** — (Milestone 2 **COMPLETE**; Milestone 3 not started)
**Overall:** Milestone 1 **RELEASED** · Milestone 2 **✅ COMPLETE** — all **13/13 Package Tutorials LOCKED** across 14 packages (**479 public symbols documented**), Template v1.0 + Implementation Standard frozen, shared lesson-execution test (66 corpus cases) · Milestones 3-6 not started

---

## ✅ MILESTONE 2 — PACKAGE TUTORIALS: COMPLETE (2026-07-18)

**All 13 deep package tutorials LOCKED, covering all 14 packages.** Authored to
Package Tutorial Template v1.0 under the frozen Implementation Standard; **479
public API symbols documented** (100% of every package `__all__`, coverage-acceptance
verified); every tutorial independently validated (coverage · ruff · format ·
mypy --strict · pytest · mkdocs --strict · check_docs) and per-tutorial LOCKED.
Unit A (Foundation): core, ontology, events, registry&plugins, connectors. Unit B
(Intelligence): kpis, analytics, decision, digital_twin, simulation, optimization,
agents, visualization. `src/` never modified. Shared lesson-execution smoke test
guards the whole corpus (66 cases). See the Milestone 2 Completion Report below and
per-tutorial LOCK records in the progress table.

---

## Milestone 2 - Package Tutorials (architecture phase)

**Status:** Architecture designed, documented, and validated (docs build clean).
No lessons/tutorials/code written; `src/` untouched. Design lives in
[`architecture/M02_PACKAGE_TUTORIALS.md`](architecture/M02_PACKAGE_TUTORIALS.md).

**Design summary:**
- **Scope:** 13 package tutorials in 2 units - *Foundation at depth* (core,
  ontology, events, registry&plugins, connectors, kpis) and *Intelligence at
  depth* (analytics, decision, digital_twin, simulation, optimization, agents,
  visualization). **All 14 packages are in scope** - `registry`, `plugins`,
  `connectors` were added by Decision D1 (Option A) and the roadmap M2 line is
  now synchronized (§1 of the architecture doc; roadmap Revision History 2026-07-18).
- **Depth model:** full public API + integration + the package's extension
  point, vs M1's single-concept intro. Plugin authoring is *woven* into each
  interface-only package's "How to extend" section (reusing `05_plugin_*`
  examples), not a separate unit.
- **New examples required (~6-10):** analytics (no `examples/` dir), plugins
  (no dir), plus deeper KPIEngine/connector scripts. Everything else reuses
  existing demos.
- **Key new-for-M2 validation:** an automated `pytest` lesson-execution test
  covering M1+M2 (closes M1's top Class-B item E2; prevents corpus rot).
- **Phasing (resumable):** M2a = Unit A (6 tutorials) · M2b = Unit B (7).

### Architecture Review (Lead Architect) - COMPLETE

**Outcome:** ✓ **Ready after Architecture Corrections** · **Readiness score 9/10**.
Five-perspective review (Architectural / Educational / Mining / Engineering /
Release). All 14 cited API counts re-verified against `__all__` (exact match);
§4 reuse filenames verified present; missing `analytics`/`plugins` dirs
confirmed. Doc is production-grade and governance-clean.

**Doc convention adopted** (per user governance rec): milestone-architecture docs
now live at `docs/learning/architecture/M0X_*.md`. This doc = `M02_PACKAGE_TUTORIALS.md`.

**Required corrections (5) before "Ready for Implementation":**
1. Resolve Option A/B scope decision (the one gating item).
2. §4 table omits `simulation` - add it (reuse `examples/simulation/04_plugin_simulation_model.py`; simulation IS interface-only).
3. Reuse counts: `kpis` 4→5, `decision` 4→5 (verified 5 each).
4. §4 heading: `kpis`/`connectors` are not "interface-only" - retitle the extension-point framing.
5. §2: state the M1-prerequisite that justifies teaching registry&plugins (position 4) before Unit B motivates it.

### Decisions & Freeze (2026-07-18)

- **D1 · Scope - APPROVED (Option A):** M2 = **13 tutorials over 14 packages**
  (adds `registry`, `plugins`, `connectors`). Architecture updated throughout.
- **D2 · Corrections - APPROVED & APPLIED (all 5):** (1) `simulation` added to
  §4 plugin table; (2) reuse counts fixed (`kpis` 4→5, `decision` 4→5);
  (3) §4 "interface-only" wording split into interface-only / concrete-with-a-seam;
  (4) §2 registry&plugins mechanism-before-motivation prerequisite stated;
  (5) §8 per-tutorial LOCK checkpoint cadence made explicit.
- **Freeze consistency pass:** fixed R3 miscount ("Five"→"Six packages"), §0 count
  line, DoD hedge; R1 marked RESOLVED. No `[proposed]` remnants, no placeholders,
  no contradictions. `mkdocs --strict` 0 warnings · `check_docs` passed.

**STATUS: ✓ ARCHITECTURE FROZEN.**

**Governance gate - CLEARED (2026-07-18):** the `LEARNING_ROADMAP.md` M2-scope
line was synchronized 11 → 14 packages (added `registry`, `plugins`,
`connectors` after `events`) and recorded in the roadmap's new Revision History.
Only that one scope cell changed; milestone ordering, dependencies, governance,
philosophy, and milestones 1 & 3-6 are untouched.

### Implementation Authorization

| Gate | State |
|---|---|
| **Architecture Status** | ✓ **Frozen** ([`architecture/M02_PACKAGE_TUTORIALS.md`](architecture/M02_PACKAGE_TUTORIALS.md)) |
| **Roadmap Status** | ✓ **Synchronized** (14 packages; Revision History 2026-07-18) |
| **Cross-document consistency** | ✓ **Verified** (roadmap ↔ progress ↔ architecture: counts, chains, numbering, terminology agree) |
| **Implementation Status** | ✓ **Authorized** |
| **Current Phase** | **Milestone 2A - Tutorial 1 (Core) ✓ LOCKED** · next: Tutorial 2 (Ontology), not started |

**CHECKPOINT (2026-07-18) - Governance synchronization COMPLETE.** Roadmap,
architecture, and progress tracker are fully synchronized: M2 scope = 14 packages
/ 13 tutorials in all three; roadmap Revision History records the 11→14 amendment;
`mkdocs --strict` 0 warnings; `check_docs` passed. Milestone 2 implementation is
**authorized**.

### Package Tutorials progress (Milestone 2)

**Implementation contract:** all tutorials follow the frozen
[`PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md`](PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md)
(process) + Package Tutorial Template v1.0 (structure, architecture §11). Future
tutorials are commissioned with only *package* + *number*.

| # | Tutorial | Page | Reuse | Validation | Status |
|---|---|:--:|:--:|:--:|---|
| 1 | Core (deep) | `tutorials/packages/01_core.md` | `examples/core/` (6) | ☑ | ☑ **LOCKED** |
| 2 | Ontology (deep) | `tutorials/packages/02_ontology.md` | `examples/ontology/` (3) | ☑ | ☑ **LOCKED** |
| 3 | Events (deep) | `tutorials/packages/03_events.md` | `examples/events/` (3) | ☑ | ☑ **LOCKED** |
| 4 | Registry & Plugins (deep) | `tutorials/packages/04_registry_and_plugins.md` | `examples/registry/` (2) + `examples/plugins/` (2 **new**) | ☑ | ☑ **LOCKED** |
| 5 | Connectors (deep) | `tutorials/packages/05_connectors.md` | `examples/connectors/` (2 + 1 **new**) | ☑ | ☑ **LOCKED** |
| — | **UNIT A (Foundation) COMPLETE** | core · ontology · events · registry&plugins · connectors | | | ✅ **6/6** |
| 6 | KPIs (deep) — *opens Unit B* | `tutorials/packages/06_kpis.md` | `examples/kpis/` (4) | ☑ | ☑ **LOCKED** |
| 7 | Analytics (deep) | `tutorials/packages/07_analytics.md` | `examples/analytics/` (**3 new**, R2) | ☑ | ☑ **LOCKED** |
| 8 | Decision (deep) | `tutorials/packages/08_decision.md` | `examples/decision/` (4) | ☑ | ☑ **LOCKED** |
| 9 | Digital Twin (deep) | `tutorials/packages/09_digital_twin.md` | `examples/digital_twin/` (4) | ☑ | ☑ **LOCKED** |
| 10 | Simulation (deep) | `tutorials/packages/10_simulation.md` | `examples/simulation/` (4) | ☑ | ☑ **LOCKED** |
| 11 | Optimization (deep) | `tutorials/packages/11_optimization.md` | `examples/optimization/` (5) | ☑ | ☑ **LOCKED** |
| 12 | AI Agents (deep) | `tutorials/packages/12_agents.md` | `examples/agents/` (5) | ☑ | ☑ **LOCKED** |
| 13 | Visualization (deep) | `tutorials/packages/13_visualization.md` | `examples/visualization/` (5) | ☑ | ☑ **LOCKED** |

**13 / 13 package tutorials complete — ✅ MILESTONE 2 COMPLETE.**

#### Tutorial 13 - Visualization (deep): LOCK record (2026-07-18)
Template v1.0, 16 sections; **21 [deep] / 8 [ref]** (29/29 documented). **Final tutorial.**
§3 integrates every layer (presents governed evidence: kpis card + optimization plan +
agent note + simulation playback) + registry (**dual `REGISTRY`/`RENDERERS`**) + core
(`PresentationModel` = structure, no bytes). Interface-only (ships zero views/renderers;
charting lib in the plugin, ADR-0012). Extension: reused `05_plugin_visualization_and_renderer.py`.
Validation: 5 reused examples exit 0; ruff/mypy clean; **pytest 3052**; mkdocs strict +
check_docs pass; `src/` untouched.
**Verified notes:** `Visualization`/`Renderer` (ABC, **interface-only**, zero-ship); `PresentationModel`
(structure, not bytes)/`RenderedOutput`; one `RenderingPipeline` (Visualization→model→Renderer);
`Widget`/`Dashboard`/`DashboardBuilder`/`Layout`/`Theme`; `Report`/`ReportBuilder`/`ExportRequest`/`ExportResult`
(export = same render path); `VisualizationContext`/`VisualizationMetadata`/`VisualizationCategory`/`RendererMetadata`;
`REGISTRY`+`register` (views), `RENDERERS`+`register_renderer` (renderers), `by_owner`/`by_theme`, `DashboardRepository`.
qualify-don't-coerce (missing evidence → warning, never 0.0). Exceptions ← core.MineProductivityError.

#### Tutorial 12 - AI Agents (deep): LOCK record (2026-07-18)
Template v1.0, 16 sections; **25 [deep] / 16 [ref]** (41/41 documented). No M1 lesson.
§3 integrates simulation+optimization (agent tools; planning agent composes them) +
decision (audited/explained results) + registry (**dual `REGISTRY`/`TOOLS`**) + core.
Interface-only (ships zero agents/tools; LLM lives in the plugin). Extension: reused
`05_plugin_agent_and_tool.py`. Validation: 5 reused examples exit 0; ruff/mypy clean;
**pytest 3047**; mkdocs strict + check_docs pass; `src/` untouched.
**Verified notes:** `Agent`/`Tool`/`AgentMemory` (ABC, **interface-only**); `Task`/`TaskStatus`/`TaskState`,
`Goal`, `TaskExecutor` (gate→act→persist→audit), `TaskRepository`; `PolicyEngine`/`AgentPolicy`/`PolicyStatus`,
`AgentCapabilitySet`/`Permission`, `ApprovalRequest`/`ApprovalStatus` (AwaitingApproval→`resume()`; deny=`PermissionDeniedError` hard stop);
`WorkflowEngine` (multi-agent decomposition), `AgentMessage`/`DelegationRequest`/`ConversationContext`/`ConversationTurn`;
`AgentResult`, `AgentAuditTrail`/`AgentAuditEntry`; `ToolInvocation`/`ToolMetadata`; `AgentMetadata`/`AgentCategory`;
`REGISTRY`+`register` (agents), `TOOLS`+`register_tool` (tools), `by_category`/`by_scope`. Exceptions ← core.MineProductivityError.

#### Tutorial 11 - Optimization (deep): LOCK record (2026-07-18)
Template v1.0, 16 sections; **23 [deep] / 13 [ref]** (36/36 documented). No M1 lesson.
§3 integrates simulation (candidate search over `ExperimentRunner`) + digital_twin
(`TwinSnapshot` seed) + analytics (PlanComparator/SensitivityAnalyzer delegate) + registry + core.
Interface-only (6 paradigm bases ship zero solvers; platform imports no solver lib). Extension:
reused `05_plugin_solver_adapter.py` (MIP adapter plugin). Validation: 5 reused examples exit 0;
ruff/mypy clean; **pytest 3042**; mkdocs strict + check_docs pass; `src/` untouched.
**Verified notes:** `OptimizationModel(ABC)` + 6 paradigm bases (`LinearProgrammingModel`,
`MixedIntegerProgrammingModel`, `ConstraintProgrammingModel`, `MultiObjectiveModel`,
`EvolutionaryMetaheuristicModel`, `NetworkOptimizationModel` — **interface-only**);
`OptimizationProblem`(`DecisionVariable`/`VariableDomain`, `Constraint`/`ConstraintOperator`,
`Objective`/`ObjectiveDirection`)/`ProblemStatus`; `OptimizationExecutor`, `OptimizationRun`/`RunStatus`, `OptimizationState`;
`OptimizationResult`(feasible + assignment), `ParetoResult` (multi-objective); `PlanComparator`, `SensitivityAnalyzer`;
`REGISTRY: registry.Registry`+`register`+`by_category`/`by_scope`; `OptimizationRunRepository`. Exceptions ← core.MineProductivityError.

#### Tutorial 10 - Simulation (deep): LOCK record (2026-07-18)
Template v1.0, 16 sections; **21 [deep] / 13 [ref]** (34/34 documented). No M1 lesson.
§3 integrates digital_twin (`seed_from_replay` from a `TwinSnapshot`) + analytics
(summaries delegate; simulation owns no statistics) + events + registry + core.
Interface-only (4 methodology bases ship zero models). Extension: reused
`04_plugin_simulation_model.py` (`MonteCarloModel` plugin). Validation: 4 reused
examples exit 0; ruff/mypy clean; **pytest 3037**; mkdocs strict + check_docs pass; `src/` untouched.
**Verified notes:** `SimulationModel(ABC)` + 4 methodology bases `MonteCarloModel`/`DiscreteEventModel`/
`SystemDynamicsModel`/`CalibrationModel` (**interface-only**); `Scenario`(versioned, parameters, horizon)/`ScenarioStatus`;
`SimulationExecutor`, `SimulationRun`/`RunStatus`, `SimulationState`/`SimulationStateCache`, `SimulationClock`/`TimeProgressionMode`;
`Experiment`/`ExperimentRunner`->`ExperimentResult` (N seeded trials); `ScenarioComparator`, `SensitivityAnalyzer`;
`seed_from_replay` (twin snapshot -> seed); `SimulationResult`; `REGISTRY: registry.Registry`+`register`+`by_category`/`by_scope`;
`SimulationRunRepository`. Exceptions ← core.MineProductivityError.

#### Tutorial 9 - Digital Twin (deep): LOCK record (2026-07-18)
Template v1.0, 16 sections; **20 [deep] / 16 [ref]** (36/36 documented). §3 integrates
events (state = `_apply` fold of the log; cold-start replay; `TwinSynchronizer` over
EventBus; `TwinSnapshot` reuses `events.AsOf`) + ontology (11 `TwinCategory` mirror
entity families) + core (`Twin(BaseEntity[str])` identity equality; `core.serialization`;
`&/|/~` discovery) + registry. Extension: reused `04_plugin_twin_type.py` (ships zero
twin types, spec 08 §27) + interface-only `TwinSimulationModel` (hook into simulation).
Validation: 4 reused examples exit 0; ruff/mypy clean; **pytest 3033**; mkdocs strict +
check_docs pass; `src/` untouched.
**Verified notes:** `Twin(BaseEntity[str], ABC)` abstract `_apply(events,*,context)->TwinState`
(**only** state-change path, no setter); `TwinCategory` 11 (MINE/EQUIPMENT/PLANT/CONVEYOR/
HAULAGE/FLEET/PROCESSING_PLANT/GEOLOGICAL/VENTILATION/STOCKPILE/PRODUCTION); `TwinStatus`
(PROVISIONED/SYNCHRONIZED/STALE/DEGRADED/RETIRED); `TwinState`/`TwinSnapshot`(schema_version)/`TwinStateCache`/`TelemetryReading`;
`SyncPolicy`+`TwinSynchronizer`->`SyncResult`; `TwinRepository`, `by_category`/`by_scope` (core specs),
`REGISTRY: registry.Registry`+`register`; `TwinSimulationModel`(ABC, interface-only)->`TwinSimulationResult`.
Exceptions ← core.MineProductivityError.

#### Tutorial 8 - Decision (deep): LOCK record (2026-07-18)
Template v1.0, 16 sections; **22 [deep] / 27 [ref]** (49/49 documented). §3 integrates
kpis + analytics (consumes `KPIResult`/`TrendResult` as evidence, never re-derives) +
events (`RealTimeDecisionSession` over EventBus) + registry + core (`Rule` IS a
`core.PredicateSpecification`). Extension: reused `examples/decision/04_plugin_strategy.py`
(a `DecisionStrategy` plugin via EntryPointDiscovery); interface-only `RootCauseAnalyzer`/
`WhatIfEngine` (ADR-0007). Validation: 4 reused examples exit 0; ruff/mypy clean;
**pytest 3029**; mkdocs strict + check_docs pass; `src/` untouched.
**Verified notes:** `DecisionModel(ABC)` (`meta: ClassVar[DecisionMetadata]`, `_decide(context)->DecisionResult`,
`decide()` orchestration); `DecisionContext` bundles KPI/analytics evidence; `DecisionCategory`
(STRATEGY/RANKING/ROOT_CAUSE/WHAT_IF). `Policy` (versioned, rules dict of `Rule=PredicateSpecification`,
thresholds, strategy_code); `Threshold`(field,comparator,limit)->`ThresholdBreach`; `DecisionPipeline`
composes `RuleEngineStage`->`ModelStage`->`ExplanationStage`->ranking; `Recommendation`(triggered_rules,
summary,evidence,explanation); `RankedRecommendation`(score,components); `Explanation`(premises);
`RankingStrategy`/`WeightedScoreRanking`; `ActionPrioritizer`/`ActionPlanner`(cycle->err)/`ActionPlan`/`ActionPriority`;
`DecisionAuditTrail`/`DecisionAuditEntry`(recorded_at); `RealTimeDecisionSession`(EventBus, latest(), rt/batch parity);
`BatchDecisionRunner`; `RootCauseAnalyzer`->`RootCauseResult`, `WhatIfEngine`->`WhatIfResult` (**interface-only**, ADR-0007);
`REGISTRY: registry.Registry` + `register`. Exceptions ← core.MineProductivityError.

#### Tutorial 7 - Analytics (deep): LOCK record (2026-07-18)
Template v1.0, 16 sections; **23 [deep] / 30 [ref]** (53/53 documented). §3 integrates
kpis (consumes `KPIResult`/`TimeSeries`, never re-derives) + events + registry + core.
Interface-only package (ADR-0006). **3 examples authored (R2 — no examples dir):**
`01_describe_and_distribution`, `02_trend`, `03_plugin_forecasting_model` (a custom
`ForecastingModel` — the extension point), all gate-clean + smoke-tested. Validation:
ruff/format/mypy clean; **pytest 3024**; mkdocs strict + check_docs pass; `src/` untouched.
**Verified notes:** `AnalyticsModel(ABC)` (`meta: ClassVar[AnalyticsMetadata]`, pure
`_analyze(series,*,context)->AnalyticsResult`; `analyze` guards `meta.min_observations`);
`AnalyticsContext(*, event_store, kpi_engine=, backend=)`; `AnalyticsMetadata(code, name=,
category=AnalyticsCategory, description=, min_observations=)`; `AnalyticsCategory`
(TREND/BASELINE/BENCHMARK/FORECASTING/ANOMALY/OUTLIER). `TimeSeries(points=(TimeSeriesPoint(timestamp,value),..))`
auto-sorted, `.values()`, `.from_kpi_results`, `.from_event_query`. Stats: `describe(series)->StatisticalSummary(n,mean,std,minimum,maximum,percentiles)`,
`percentile(values,q)`, `histogram(values,*,bins=)->Histogram(bin_edges,counts)`,
`distribution(values)->DistributionSummary(...,skewness,kurtosis,...)`, `confidence_interval(...)->ConfidenceInterval(lower,upper,confidence,method)`.
`LinearTrendModel().analyze(...)->TrendResult(slope,intercept,r_squared,direction,window)` — **slope is per SECOND**.
`ForecastingModel(AnalyticsModel, ABC)` abstract `_forecast(series,*,horizon,context)->ForecastResult(horizon,predicted,intervals)` — **interface-only**;
`AnomalyDetector`/`OutlierDetector` also interface-only. `REGISTRY: registry.Registry` + `register`.
Result types ← core.BaseValueObject; exceptions ← core.MineProductivityError.

#### Tutorial 6 - KPIs (deep): LOCK record (2026-07-18)
Template v1.0, 16 sections; **11 [deep] / 21 [ref]** (32/32 documented). Opens Unit B.
§3 integrates events (engine scans EventStore/EventQuery) + ontology (Shift window
resolution) + registry (`REGISTRY` is a `registry.Registry`; `@register`) + core.
Extension: custom `PROD.AvgPayload` (`ProductionKPI` + `KPIMetadata` + `_compute` +
`@register`), gate-clean. Validation: 4 reused examples exit 0; ruff/format/mypy
clean; **pytest 3021**; mkdocs strict + check_docs pass. `src/` untouched.
**Verified notes:** `BaseKPI` (`meta: ClassVar[KPIMetadata]`, pure `_compute(rows)->float|None`,
inherited `compute` = qualify-don't-coerce); `KPIMetadata(core.BaseMetadata)` 29-field,
validate() requires official_name/business_purpose/operational_question/business_meaning/
formula/unit/dimensions/required_events non-empty; `Aggregation`(ADDITIVE/RATIO/AVERAGE/
WEIGHTED_AVERAGE/ROLLING/CUMULATIVE/DERIVED), `Direction`, `DigitalMaturity`(L1-L4);
`KPIResult(core.BaseValueObject)` value(float|None)/unit/n/warnings/scope, `.to_frame()`;
`KPIEngine(store, registry, backend, cache, *, shifts=)` `.execute(code,*,window,scope)->Result`,
`.summary(...)`; `DependencyGraph(REGISTRY).topological_order(code)`; `REGISTRY: Registry[str,type[BaseKPI]]`
+ `register` (dup->`KPIVersionConflictError`, cycle->`KPICircularDependencyError` at registration);
9 category bases (ProductionKPI etc., `__init_subclass__` enforces namespace); `ResultCache`;
`KPIIdentifier`/`parse_identifier`; `KPIStatus`(PROPOSED/ACTIVE/DEPRECATED/RETIRED);
`Window`/`RollingWindow`/`CumulativeWindow`. Exceptions ← core (KPIVersionConflictError ← registry.RegistrationError).

**Shared infrastructure LANDED (Tutorial 2), extended each lock:** the automated
lesson-execution test `tests/smoke/test_learning_suite_examples.py` (architecture
§7 / standard §4) runs every M1 lesson (10) + every locked Package Tutorial's
examples (core 6, ontology 3, events 3, registry 2, plugins 2, connectors 3, kpis 4, analytics 3, decision 4, digital_twin 4, simulation 4, optimization 5, agents 5, visualization 5) as
subprocesses asserting exit `0` - **66 cases, all green**. To extend: append the
package dir to `PACKAGE_TUTORIAL_EXAMPLE_DIRS` when a tutorial locks.

#### Tutorial 2 - Ontology (deep): LOCK record (2026-07-18)

**Implementation complete.** `docs/tutorials/packages/02_ontology.md`, Template v1.0
(16 sections, **substantive §3 Integration** - ontology→core). Teaches the **entire
56-symbol surface** via the coverage convention: **19 [deep]** (spine +
representative leaves) / **37 [ref]** (family-grouped table; all named,
partition verified). Extension point taught with a runnable, gate-clean
`ElectricRopeShovel` leaf (`@register_equipment` → resolvable by `OntologyValidator`
→ `to_schema()`).

**Validation results (all green):**
- `ruff` / `ruff format --check` / `mypy --strict` - clean on all 3 reused
  `examples/ontology/*.py`, the `ElectricRopeShovel` extension example, **and** the
  new `tests/smoke/test_learning_suite_examples.py`.
- Every reused script executed (exit `0`); output pasted **verbatim**.
- Coverage acceptance test: **56/56** public symbols documented (none missing).
- `pytest` - **3006 passed** (full suite; +20 lesson-execution cases vs Tutorial 1's 2986).
- `mkdocs build --strict` - 0 warnings. `check_docs.py` - passed.

**Files changed:** `docs/tutorials/packages/02_ontology.md` (new);
`tests/smoke/test_learning_suite_examples.py` (new, shared infra); `mkdocs.yml`
(nav: `02 · Ontology (deep)`; legacy Ontology relabelled); `docs/tutorials/index.md`.
**`src/`, `examples/` untouched.**

**Verified `ontology` API notes (carry-forward):**
- `BaseEntityType(core.BaseEntity[str], ABC)` - adds its **own** `__post_init__`→
  `_normalize()`/`validate()` (core.BaseEntity has none); declares `code: ClassVar[str]`
  + `meta: ClassVar[EntityTypeMetadata]`; `to_schema()` (cached per type).
- `EntityTypeMetadata(core.BaseMetadata)` adds `supported_kpis`, `parent_code`.
- **`register_equipment`** is the public alias of internal `register_entity_type`;
  the registry lookups (`lookup_entity_type`/`get_entity_type`/…) are **NOT** public.
- `RelationshipKind` = 5 members: `BELONGS_TO`, `PART_OF`, `OPERATED_BY`,
  `LOCATED_AT`, `SCOPED_TO`. `Relationship(source_id, kind, target_id)` is a value object.
- `Mine(id, commodity_codes=(...), method=)` - **plural** `commodity_codes`.
  `Pit(id, mine_id, commodity)`, `Bench(id, pit_id, elevation_m)`,
  `Shift(id, mine_id, pattern, start_utc, end_utc, scheduled_h)` + `.contains(dt)`.
  `Fleet(id, mine_id, equipment_type_code)`. `EquipmentType.rated_capacity` (+ shared
  `operational_states`) is the only guaranteed leaf field.
- `OntologyValidator(core.BaseValidator)` → `core.ValidationResult`, **never raises**;
  `*_type_code` resolves against the registry, `*_id` needs an injected `entity_resolver`.
- `KnowledgeGraphProjection` (ABC: `nodes()`/`edges()`), `GraphNode(node_id, node_kind, entity_type_code=)`,
  `GraphEdge(source_id, target_id, edge_kind)`.
- Exceptions extend core: `OntologyValidationError(ValidationError)`,
  `UnknownEntityTypeError(NotFoundError)`, `RelationshipError(MineProductivityError)`.
- `__all__` is alphabetically sorted (enforced by `tests/unit/ontology/test_public_api.py`).
- Design refs: AD-ON-02 (edges not nesting), AD-ON-03 (governed taxonomies live here),
  AD-ON-04 (operational state is a twin concern), §19 (validation at construction).

#### Tutorial 1 - Core (deep): LOCK record (2026-07-18)

**Independently reviewed → refined → re-locked as the Template v1.0 reference.**
Review verdict: Template Approved after Corrections (9/10). All three approved
refinements applied: (1) coverage convention ([deep]/[ref], all 38 symbols
documented, 8 [ref] in a new "Reference coverage" subsection); (2) **Integration
with adjacent layers** section added (§3, "N/A - foundational layer" for Core);
(3) architecture synchronized to **Package Tutorial Template v1.0** (§11).

**Implementation complete.** `docs/tutorials/packages/01_core.md` (**16-section
Template v1.0** + Objective/Prerequisites/Further-reading). Teaches the **entire
38-symbol `core` public surface**, public APIs only, building on M1 L02/L03
without repeating them. Extension point (`BaseRepository`) taught with a runnable,
gate-clean `FleetRepository` example.

**Validation results (all green):**
- `ruff check` · `ruff format --check` · `mypy --strict` - clean on all 6 reused
  `examples/core/*.py` **and** the inline `FleetRepository` extension example.
- Every reused script executed (exit `0`); output pasted **verbatim** into the tutorial.
- `pytest` - **2986 passed** (full suite; no regression).
- `mkdocs build --strict` - 0 warnings. `check_docs.py` - 0 broken / 0 failed.

**Files changed:** `docs/tutorials/packages/01_core.md` (new); `mkdocs.yml` (new
"Package Tutorials" nav group + relabelled reference walkthroughs); `docs/tutorials/index.md`
(new Package Tutorials subsection). **`src/`, `examples/`, `tests/` untouched.**

**Lessons learned (carry-forward for Tutorials 2–13):**
- **Format is now Package Tutorial Template v1.0 (16 sections).** RESOLVED: the
  richer package-tutorial format was independently reviewed, refined, and promoted
  to **Template v1.0** (architecture §11). It adds an **Integration with adjacent
  layers** section (§3; "N/A - foundational" for Core, mandatory for 2–13) and a
  **coverage convention** (every `__all__` symbol tagged [deep] or [ref], none
  undocumented). Architecture "eleven-section" wording updated throughout. The
  earlier "wording lag" item is closed.
- **Placement:** deep tutorials live at `docs/tutorials/packages/NN_<pkg>.md`
  (parallel to `fundamentals/`), wired under a new nav "Package Tutorials" group.
  Legacy thin per-package pages (`tutorials/<pkg>.md`, README-includes) kept as
  relabelled "API walkthroughs (reference)" to avoid a destructive edit; they can
  be retired package-by-package as each deep tutorial lands.
- **Reuse-first held:** Core needed **no new example script** - the 6 existing
  demos cover the surface; the extension example is taught inline (verified in
  scratchpad), matching M1's inline-snippet style. Expect Tutorial 2 (Ontology)
  to be reuse-only too; analytics/plugins will need new scripts (Risk R2).
- **Automated lesson-execution test (arch §7):** LANDED in Tutorial 2 at
  `tests/smoke/test_learning_suite_examples.py` (retrofits M1 + Core + Ontology).

#### Verified `core` API notes (carry-forward)

- `BaseEntity[TId]`: **`eq=False` must be repeated on every concrete subclass**
  (dataclass regenerates `__eq__` on the subclass, shadowing identity equality).
  Equality/hash = `(type, id)`.
- `BaseValueObject`: runs `_normalize()` then `validate()` in `__post_init__`;
  frozen, so `_normalize` assigns via `object.__setattr__`; `replace(**changes)`
  re-runs both.
- `BaseRepository[TEntity, TId]`: 5 abstract methods (`add`/`get`/`find`/`remove`/`list`)
  + free `__contains__`. `get`→`NotFoundError`; `find`→`Maybe`; `add`→`DuplicateError`.
- `BaseSpecification`: compose with `&` / `|` / `~`; `PredicateSpecification(callable)`
  for one-offs; combinators short-circuit.
- `BaseFactory.create_result(...)` / `BaseBuilder.build_result()` return `Result`
  (exception-free variants).
- `ValidationResult`: `.success()` / `.failure(*errs)` / `.is_valid` / `.errors` /
  `.merge()` / `.raise_if_invalid()`; `CompositeValidator(*v)` accumulates all errors.
- `Result`: `ok`/`err`/`is_ok`/`is_err`/`value`/`error`/`unwrap`/`unwrap_or`/
  `unwrap_or_else`/`map`/`map_err`/`and_then`. `err(str)` wraps in `MineProductivityError`.
- `Maybe`: `some`/`nothing`/`is_some`/`is_nothing`/`unwrap`/`unwrap_or`/
  `unwrap_or_else`/`map`/`and_then`/`filter`/`to_result(error)`.
- Exception hierarchy root = `MineProductivityError(message, *, details=)`; subclasses
  `ValidationError`, `ConfigurationError`, `NotFoundError`, `DuplicateError`,
  `SerializationError`, `BuilderError`.
- `core.__all__` = 38 symbols (verified). No dedicated `core` architecture spec or
  ADR exists (handbook specs start at Events); "Further reading" points to the
  handbook README, API reference, package guide, and M1 L02/L03.

#### Tutorial 3 - Events (deep): LOCK record (2026-07-18)

**Implementation complete.** `docs/tutorials/packages/03_events.md`, Template v1.0
(16 sections, **richest §3 Integration yet** - events builds on **both** core and
ontology). Teaches the **entire 31-symbol surface**: **15 [deep]** (payload/
envelope/store/replay/validation spine) / **16 [ref]** (other payloads, bus,
schema, taxonomies, exceptions). Extension point taught with a runnable, gate-clean
`BlastEvent` (custom `BaseEvent` flowing through the same validator/envelope/store).

**Validation results (all green):**
- `ruff` / `ruff format --check` / `mypy --strict` - clean on all 3 reused
  `examples/events/*.py` and the `BlastEvent` extension example.
- Every reused script executed (exit `0`); output pasted **verbatim**.
- Coverage acceptance: **31/31** public symbols documented.
- `pytest` - **3009 passed** (smoke test now covers events -> 23 corpus cases).
- `mkdocs build --strict` - 0 warnings. `check_docs.py` - passed.

**Files changed:** `docs/tutorials/packages/03_events.md` (new);
`tests/smoke/test_learning_suite_examples.py` (`+"events"`); `mkdocs.yml` (nav);
`docs/tutorials/index.md`. **`src/`, `examples/` untouched.**

**Verified `events` API notes (carry-forward):**
- `BaseEvent(core.BaseValueObject, ABC)` - `equipment_id`/`shift_id` +
  `event_type_code: ClassVar[str]` + abstract `duration_h()`. 6 canonical codes:
  CYCLE, PRODUCTION, DELAY, CONSUMPTION, MAINTENANCE, SAFETY.
- `EventEnvelope(core.BaseValueObject, Generic)` - `event_id`/`version`/`payload`/
  three UTC timestamps (`event <= processing <= ingestion`, enforced)/`metadata`.
- `EventID(core.BaseIdentifier[str])` `.generate()` (26-char ULID, time-sortable);
  `EventVersion(core.BaseVersionedObject)` `.next_version()`; `(EventID, EventVersion)` = PK.
  `EventMetadata(core.BaseMetadata)` adds confidence/source_system/late_arrival.
- `EventStore(ABC)` **specializes core.BaseRepository**: `append`->`Result`,
  `append_batch`, `get(as_of_version=)`, `find`->`Maybe`, `query`->`Iterator`,
  `replay`->`ReplayHandle`, `snapshot`->`EventSnapshot`. Reference `_InMemoryEventStore`
  is **private** (all examples use it). Idempotent on `(id, version)`; conflict -> `EventVersionConflictError`.
- `EventFilter = BaseSpecification[EventEnvelope[Any]]` (alias). `EventQuery`:
  event_types/equipment_ids/shift_ids/since_utc/until_utc/filters/as_of_version_policy.
- `EventValidator(core.BaseValidator[BaseEvent])` `.validate_with_confidence()`->
  `ValidationOutcome(result, confidence)`; `ConfidenceScore(value, reasons)` (valid=1.0;
  -0.1/error; floor 0.1). `score_confidence` NOT in top-level `__all__`.
- `AsOf(utc=|scenario=)`; `ReplayHandle(as_of, envelopes)` `.get(id)`;
  `EventSnapshot(as_of, state)`. `EventBus(ABC)` publish/`subscribe(filter: BaseSpecification, handler)`->
  `Subscription(.cancel/.is_active)`. `EventSchema.to_json_schema()`.
- **Ontology integration:** `events.SafetyEventType IS ontology.SafetyEventType`
  (re-export); `DelayEvent` uses ontology `DelayCategory`; `equipment_id`/`shift_id`
  are ontology references (AD-ON-03). Events-local enums: `ResourceType`, `SafetySeverity`.

#### Tutorial 4 - Registry & Plugins (deep): LOCK record (2026-07-18)

**Implementation complete.** `docs/tutorials/packages/04_registry_and_plugins.md`,
Template v1.0 (16 sections). **First combined two-package tutorial** (the
extensibility subsystem) and **first `[+D1]` unit**. Teaches the **entire 19-symbol
surface** (registry 11 + plugins 8): **13 [deep]** / **6 [ref]**. §1/§3 carry their
own why-before-how (no M1 lesson). Extension point = **custom plugin development**
end to end (host `Registry` + `@register` -> `PluginManifest` -> lifecycle ACTIVE),
runnable + gate-clean.

**New examples authored (Risk R2 - plugins had no example dir):**
`examples/plugins/01_manifest_and_lifecycle.py`, `examples/plugins/02_activation_order.py`,
`examples/plugins/README.md` - project style, executed (exit `0`), gate-clean, added
to the smoke test.

**Validation results (all green):**
- `ruff` / `ruff format --check` / `mypy --strict` - clean on all 4 examples
  (registry 2 reused + plugins 2 new) and the extension example.
- Every example executed (exit `0`); output pasted **verbatim** (stdout).
- Coverage acceptance: **19/19** public symbols documented (registry 11 + plugins 8).
- `pytest` - **3013 passed** (smoke test now 27 corpus cases).
- `mkdocs build --strict` - 0 warnings. `check_docs.py` - passed.

**Files changed:** `docs/tutorials/packages/04_registry_and_plugins.md` (new);
`examples/plugins/` (**3 new files**); `tests/smoke/test_learning_suite_examples.py`
(`+"registry"`, `+"plugins"`); `mkdocs.yml` (nav); `docs/tutorials/index.md`.
**`src/` untouched.**

**Verified `registry`+`plugins` API notes (carry-forward):**
- Dependency order: `core -> ontology -> events -> registry -> plugins`. `registry`
  is the mechanism every package **above** it specializes; `ontology` sits **below**
  it, so it carries its own internal type registry (can't import `registry`).
- `Registry(name=)[K,V]` - **structural echo of core.BaseRepository**; `register(key,
  item, metadata=)`->`Result` (**add-only**, dup->`DuplicateRegistrationError`),
  `lookup`->`Maybe`, `get`->raises `UnregisteredLookupError`, `list(spec)`,
  `metadata_for`->`Maybe`, `__contains__/__len__/__iter__`.
- `registered_in(registry, key_of=, metadata_of=)` -> `@register` decorator factory.
- `EntryPointSpec(group, target_registry)` (BaseValueObject); `EntryPointDiscovery().discover(spec)`
  ->`Result[Sequence[str]]` (**isolation**: one bad entry-point skipped). `DiscoveryCache`
  memoizes per spec (`get_or_discover`, `invalidate`).
- `VersionRange(min_version, max_version_exclusive)` half-open; `VersionCompatibility.is_compatible(range, ver)`
  / `.check_or_raise(...)` (static). Version parse = leading-digit, dependency-free.
- `PluginManifest(plugin_name, plugin_version, core_version_range: VersionRange,
  provides: tuple[EntryPointSpec], depends_on=tuple[PluginDependency])`;
  `PluginDependency(plugin_name, version_range)`.
- `PluginState` = DISCOVERED/VALIDATED/ACTIVE/FAILED/DEACTIVATED. `PluginLifecycle(ABC)`
  activate/deactivate/state_of; reference `_DefaultPluginLifecycle(core_version=, loader=)`
  is **private**. `PluginLoader.load(manifest)`->`Result[Mapping[group, names]]`.
- `resolve_activation_order(manifests)`->`Result` (Kahn topo-sort; missing dep / cycle
  -> `PluginDependencyError`). Exceptions ← core: RegistrationError/DuplicateRegistrationError/
  VersionIncompatibleError (via MineProductivityError), UnregisteredLookupError (via NotFoundError),
  PluginActivationError/PluginDependencyError (via MineProductivityError).

#### Tutorial 5 - Connectors (deep): LOCK record (2026-07-18)

**Implementation complete.** `docs/tutorials/packages/05_connectors.md`, Template
v1.0 (16 sections). **Completes Unit A (Foundation).** Second `[+D1]` unit. Teaches
the **entire 25-symbol surface**: **13 [deep]** / **12 [ref]**. §3 is the **richest
integration in the suite** - connectors unites all four packages below it (core +
ontology + registry + events). Extension point = custom `FMSConnector`.

**New example authored (Example Coverage Rule + emphasis):**
`examples/connectors/03_custom_connector.py` - a self-contained `DispatchLogConnector`
(custom `FMSConnector` + `@register_connector`), executed (exit `0`), gate-clean,
added to the smoke test. (Connectors already had 2 examples, so the rule did not
strictly require a new one; authored to make the extension point a permanent,
smoke-tested artifact.)

**Validation results (all green):**
- `ruff` / `ruff format --check` / `mypy --strict` - clean on all 3 connectors examples.
- Every example executed (exit `0`); output pasted **verbatim** (stdout).
- Coverage acceptance: **25/25** public symbols documented.
- `pytest` - **3016 passed** (smoke test now 30 corpus cases).
- `mkdocs build --strict` - 0 warnings. `check_docs.py` - passed.

**Files changed:** `docs/tutorials/packages/05_connectors.md` (new);
`examples/connectors/03_custom_connector.py` (**new**);
`tests/smoke/test_learning_suite_examples.py` (`+"connectors"`); `mkdocs.yml` (nav);
`docs/tutorials/index.md`. **`src/` untouched.**

**Verified `connectors` API notes (carry-forward):**
- `FMSConnector(ABC)` - the extension point; `name: ClassVar[str]`,
  `supported_modes: ClassVar`. Only `get_cycle_data`/`get_delay_data` abstract
  (AD-CN-01); other four `get_*_data` default to `iter(())`. All must be **lazy**
  generators. `health_check()`->`ConnectorHealth`; `provided_event_types()` classmethod.
- `IngestionMode` = BATCH/INCREMENTAL/STREAMING. `HealthStatus` = HEALTHY/DEGRADED/
  UNHEALTHY/UNKNOWN. `ConnectorHealth(status, last_successful_pull_utc=, detail=)` (BaseValueObject).
- **Registry integration (T4):** `CONNECTORS: Registry[str, type[FMSConnector]]`;
  `register_connector = registered_in(CONNECTORS, key_of=lambda cls: cls.name)`;
  `get_connector(name)`->type (raises UnregisteredLookupError). 6 reference connectors:
  csv, excel, rest, graphql, kafka, mqtt. `CSVConnector(path=, shift_id=, delay_path=)`,
  `RestConnector(base_url, auth, retry, shift_id=)`.
- **Resilience:** `RetryPolicy(core.BaseConfiguration)` (max_attempts, backoff,
  base_delay_s, retryable_exceptions; `.compute_delay`, `.is_retryable`);
  `BackoffStrategy` = FIXED/EXPONENTIAL/EXPONENTIAL_JITTER. `AuthProvider(ABC)`
  credentials()/refresh()->Result; `Credentials(token, expires_at_utc=)`; reference
  `_StaticAuthProvider` **private**. (`run_with_retry` module-public, NOT in top-level `__all__`.)
- **Normalization (ontology integration):** `FieldMapper(mapping)` `.apply(raw)`;
  `ReasonCodeMap(vendor_name, mapping{code:(ontology.DelayCategory, reason)})` `.resolve`->Maybe;
  `Normalizer(ABC)` normalize_cycle/normalize_delay->events.
- **Events integration (T3):** every `get_*_data` yields canonical `events`
  (CycleEvent/DelayEvent/...). Connectors is the ingestion boundary: **connectors
  ingest -> events record -> intelligence derives.**
- Exceptions ← core.MineProductivityError: `ConnectorError` (root), `MappingError`,
  `AuthenticationError`, `SourceUnavailableError` (default retryable), `ContractViolationError`.

**CHECKPOINT (2026-07-18) - Tutorial 5 (Connectors) COMPLETE & LOCKED; UNIT A DONE.**
Tutorials 1-5 LOCKED to Template v1.0 → **Unit A (Foundation) complete (6/6 packages:
core, ontology, events, registry, plugins, connectors)**. Lesson-execution guard
covers M1 + 5 tutorials (**3016 tests**, 30 corpus cases). Roadmap <-> architecture
<-> progress synchronized; `mkdocs --strict` 0 warnings, `check_docs` passed. Do not
modify a locked tutorial without a recorded defect. **Next task:** Tutorial 6 - KPIs
(deep), which **opens Unit B (Intelligence)**; verify `kpis.__all__` + `examples/kpis/*`
(5) first; substantive §3 (kpis consumes ontology + events, produces the KPIResults
analytics/decision consume); append `"kpis"` to the smoke test on lock.
**Not started - awaits go-ahead.**

---

### Release Candidate (RC1) - release-preparation phase (docs only)

Five consolidated RC tasks executed; no lesson/tutorial/production change.

| Task | Scope | Files |
|---|---|---|
| **RC-01** Discoverability | Surface the Suite from every entry point | `README.md`, `docs/index.md`, `docs/getting-started/next-steps.md`, `examples/README.md` |
| **RC-02** Doc consistency | Align the `18.33` → `733.33` first-number contradiction | `README.md`, `docs/getting-started/installation.md`, `docs/getting-started/quick-start.md` |
| **RC-03** Internal docs | Exclude the engineering tracker from the published site | `mkdocs.yml` (`exclude_docs: learning/LEARNING_PROGRESS.md`) |
| **RC-04** Roadmap cross-ref | Link project `ROADMAP.md` ↔ Learning Suite | `ROADMAP.md` |
| **RC-05** Release comms | Changelog entry + release notes + nav | `CHANGELOG.md`, `docs/releases/LEARNING_SUITE_v1.0.md`, `mkdocs.yml` |

**RC validation:** `mkdocs build --strict` 0 warnings · `check_docs.py` 0 broken /
0 failed (README snippets re-executed, now emit 733.33) · funnel verified from
README/PyPI, docs home, Getting Started, Next Steps, examples index, and ROADMAP.
Lessons/tutorials/`src/` untouched. `LEARNING_ROADMAP.md` remains LOCKED.


Legend: ☑ done & validated (LOCKED) · ◐ in progress · ☐ not started

---

## Milestone 1 - Fundamentals

### Lessons (`examples/fundamentals/`)

| # | Lesson | Script | ruff | format | mypy --strict | executes | Status |
|---|---|---|:--:|:--:|:--:|:--:|---|
| 01 | Hello MineProductivity | `01_hello_mineproductivity/hello.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 02 | Entities | `02_entities/entities.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 03 | Value objects | `03_value_objects/value_objects.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 04 | Events | `04_events/events.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 05 | Ontology | `05_ontology/ontology.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 06 | KPIs | `06_kpis/kpis.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 07 | Analytics | `07_analytics/analytics.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 08 | Decision | `08_decision/decision.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 09 | Digital Twin | `09_digital_twin/digital_twin.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 10 | Visualization | `10_visualization/visualization.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |

**10 / 10 lessons complete.** All LOCKED.

### Tutorials (`docs/tutorials/fundamentals/`)

| # | Tutorial | Status |
|---|---|---|
| 01 | `01_hello.md` | ☑ **LOCKED** |
| 02 | `02_entities.md` | ☑ **LOCKED** |
| 03 | `03_value_objects.md` | ☑ **LOCKED** |
| 04 | `04_events.md` | ☑ **LOCKED** |
| 05 | `05_ontology.md` | ☑ **LOCKED** |
| 06 | `06_kpis.md` | ☑ **LOCKED** |
| 07 | `07_analytics.md` | ☑ **LOCKED** |
| 08 | `08_decision.md` | ☑ **LOCKED** |
| 09 | `09_digital_twin.md` | ☑ **LOCKED** |
| 10 | `10_visualization.md` | ☑ **LOCKED** |

**10 / 10 tutorials complete.** All LOCKED.

### Milestone-level validation

| Task | Status |
|---|---|
| Navigation updated (`mkdocs.yml` + tutorial hub) | ☑ **DONE** |
| `mkdocs build --strict` (0 warnings) | ☑ **PASS** - 0 warnings |
| `check_docs.py` (0 broken links, 0 failed snippets) | ☑ **PASS** - 0 broken, 0 failed |
| Full `pytest` suite green (no regression) | ☑ **PASS** - 2,986 passed |
| `src/` unmodified | ☑ verified - production untouched |
| Examples verified (all execute, exit 0) | ☑ **10 / 10** |

---

## Verified API notes (carry forward)

Recorded so future sessions do not re-derive or re-guess. Each was read from the
implementation or an existing example, not recalled.

| Concept | Verified signature / fact | Source |
|---|---|---|
| `BaseEntity` subclass | must declare `@dataclass(frozen=True, slots=True, eq=False)` - `eq=False` is mandatory or dataclasses replaces identity equality | `examples/core/01_entity_and_value_object.py` |
| `Mine` | `Mine(id=, commodity_codes=("copper",), method="open_pit")` - **not** `commodity_code`/`country` | `examples/ontology/02_structural_modelling.py` |
| `Pit` / `Bench` | `Pit(id=, mine_id=, commodity=)` · `Bench(id=, pit_id=, elevation_m=)` | same |
| `Relationship` | `Relationship(source_id=, kind=RelationshipKind.BELONGS_TO, target_id=)` - **`BELONGS_TO`**, not `PART_OF` | same |
| `Shift` | `Shift(id=, mine_id=, pattern=, start_utc=, end_utc=, scheduled_h=)`; has `.contains(dt)` | same |
| KPI direct compute | `REGISTRY.get("PROD.TPH")().compute([{"payload_t": .., "operating_h": ..}])` → `KPIResult(value, unit, code, n, warnings)` | `README.md`, lesson 01 |
| `KPIEngine` wiring | `KPIEngine(store=, registry=REGISTRY, backend=PandasBackend(), cache=ResultCache(), shifts={id: Shift})`; `engine.execute(code, window="shift", scope={"shift": id})` → `Result` (`.is_ok`, `.unwrap()`) | `examples/kpis/_dataset.py` |
| Composite `UTIL.OEE` | needs the **engine** (resolves dependencies); not computable via bare `.compute(rows)` | `examples/kpis/02_composite_oee.py` |
| Event append | `EventEnvelope(event_id=EventID.generate(), version=EventVersion(), payload=, event_time_utc=, processing_time_utc=, ingestion_time_utc=, metadata=EventMetadata(name=, source_system=))`; `store.append(env).is_ok` | `examples/events/01_first_event.py` |
| Twin subclass | override `_apply(self, events, *, context) -> TwinState`; `meta: ClassVar[TwinMetadata]`; `twin.with_state(state, status=TwinStatus.SYNCHRONIZED)` | `examples/digital_twin/01_provision_and_sync.py` |
| Interface-only ABCs | `analytics.ForecastingModel` / `AnomalyDetector` / `OutlierDetector`, `decision.RootCauseAnalyzer`/`WhatIfEngine`, `visualization.Visualization`/`Renderer` ship **zero** concrete subclasses by design (ADR-0006/0007/0012). Lessons must subclass them locally, never expect a built-in. | ADRs; `src/mineproductivity/analytics/forecasting.py` |
| KPI metadata | `REGISTRY.get(code).meta` → `.code`, `.official_name`, `.aggregation` (enum), `.business_purpose`, `.operational_question`, `.formula`, `.unit`, `.direction` (enum), `.required_events`, `.dependencies` | `examples/kpis/04_discovery.py` |
| Leaf vs composite | `issubclass(REGISTRY.get(code), CompositeKPI)`; only `UTIL.OEE` is composite in the 12-KPI Standard Library | same |
| `DependencyGraph` | `DependencyGraph(REGISTRY).topological_order("UTIL.OEE")` → `['UTIL.PA','UTIL.UA','UTIL.Performance','UTIL.OEE']`. Works **without** an engine. | `examples/kpis/02_composite_oee.py` |
| `KPIResult` | `KPIResult(code, value: float\|None, unit, *, n=0, warnings=(), scope={})` | introspection |
| `Aggregation` | exported from `mineproductivity.kpis`; members: `ADDITIVE`, `RATIO`, `AVERAGE`, `WEIGHTED_AVERAGE`, `ROLLING`, `CUMULATIVE`, `DERIVED` | introspection |
| `combine_results` | **not** a top-level export - `from mineproductivity.kpis.aggregation import combine_results`. Signature: `combine_results(results: Sequence[KPIResult], aggregation: Aggregation, *, code: str, unit: str) -> KPIResult` | introspection |
| **RATIO guardrail** | `combine_results(..., Aggregation.RATIO, ...)` **raises `KPIAggregationError`** ("ratio KPIs cannot be combined by averaging already-computed results - re-derive from the union of raw rows instead"). It does *not* compute a weighted mean. Correct path: re-`compute()` over the union of raw rows. Canonical numbers: 1,300 t/h (12 h) + 1,100 t/h (6 h) → naive 1,200 **wrong**, re-derived **1,233.3** correct. | `src/mineproductivity/kpis/aggregation.py:46`; lesson 06 |
| `KPIAggregationError` | `from mineproductivity.kpis.exceptions import KPIAggregationError` | same |
| `TimeSeriesPoint` / `TimeSeries` | `TimeSeriesPoint(timestamp: datetime, value: float, *, scope={})` · `TimeSeries(points: tuple[TimeSeriesPoint, ...])` (positional tuple, not list) | introspection |
| `describe` | `describe(series: TimeSeries) -> StatisticalSummary`; fields: `model_code`, `computed_at`, `warnings`, `n`, `mean`, `std`, `minimum`, `maximum`, `percentiles` (dict keyed by int, e.g. `percentiles[50]`) | introspection |
| `AnalyticsContext` | `AnalyticsContext(*, event_store: EventStore, kpi_engine=None, backend=None)` - **`event_store` is required**; use `_InMemoryEventStore()` in lessons | introspection |
| `LinearTrendModel` | `meta.code == "TREND.Linear"`; call `._analyze(series, context=AnalyticsContext(...)) -> TrendResult`. (`analyze()` is the public wrapper returning `AnalyticsResult`.) | introspection |
| `TrendResult` | fields: `model_code`, `computed_at`, `warnings`, `slope`, `intercept`, `r_squared`, `direction`, `window`. `direction` is `Literal['increasing','decreasing','flat']` - a **plain string, not an enum** (no `TrendDirection` export exists). | introspection |
| **Trend slope units** | `slope` is **per SECOND** - `trend.py:67` fits `x = (timestamp - origin).total_seconds()`. Raw slope prints as `-0.00` and looks like "no trend". Multiply by `12*3600` for t/h-per-12h-shift. Verified: -0.000288/s = **-12.4 t/h per shift**, r²=0.974 over a 1300→1150 t/h decline. | `src/mineproductivity/analytics/trend.py:66-67`; lesson 07 |
| `Policy` (decision) | `Policy(code=, rules={name: Rule}, thresholds={name: Threshold}, strategy_code="STRATEGY.Threshold")`; has `.version` | `examples/decision/01_pipeline_over_evidence.py` |
| `Rule` | a `core.PredicateSpecification(lambda ctx: ...)` over a `DecisionContext` | same |
| `Threshold` | `Threshold(field=, comparator="<", limit=)`; `strategy.check_thresholds(ctx)` → breaches with `.threshold`, `.observed_value` | same |
| `DecisionContext` | `DecisionContext(kpi_results=, analytics_results=, scope=, recommendations=)` | same |
| Decision pipeline | `DecisionPipeline(stages=(RuleEngineStage(policy=), ModelStage(ThresholdDecisionStrategy(policy=, severity="high"))))`; run via `BatchDecisionRunner(pipeline=, audit_trail=DecisionAuditTrail()).run(ctx)` → `Result` → `.unwrap()` → `Recommendation` (`.triggered_rules`, `.summary`, `.evidence`, `.explanation`) | same |
| Explain + rank | `DecisionPipeline(stages=(ExplanationStage(), ModelStage(WeightedScoreRanking())))` → `RankedRecommendation` (`.rank`, `.score.value`, `.score.components`, `.recommendation.explanation.premises`) | same |
| `DecisionAuditTrail` | `.query(scope={...})` → entries with `.recorded_at` | same |
| `TimeSeries.from_kpi_results` | `TimeSeries.from_kpi_results(results, timestamps=[...])` - convenient alternative to building points manually | same |
| Twin category bases | `MineTwin`, `EquipmentTwin`, `PlantTwin`, `ConveyorTwin`, `HaulageTwin`, `FleetTwin`, `ProcessingPlantTwin`, `GeologicalTwin`, `VentilationTwin`, `StockpileTwin`, `ProductionTwin` (11); `TwinCategory` has the matching members | introspection |
| `TwinState` / `TwinSnapshot` | `TwinState(attributes, captured_at, schema_version="1.0.0")` · `TwinSnapshot(twin_id, state, status, as_of)` | introspection |
| `TwinContext` | `TwinContext(*, event_store, kpi_results=(), analytics_results=(), decision_results=(), as_of=None)` | introspection |
| `TwinSynchronizer` | `.synchronize(twin_id, events: Sequence[BaseEvent], *, context) -> SyncResult` (`.previous_status`, `.new_status`, `.events_applied`) | introspection |
| **`AsOf.utc` is optional** | typed `datetime \| None` - needs a narrowing `assert` before `.isoformat()` under `mypy --strict` | lesson 09 |
| `PredicateSpecification` typing | when bound to a bare variable, `mypy --strict` needs the type param: `x: PredicateSpecification[EventEnvelope[Any]] = PredicateSpecification(...)` | lesson 09 |
| Visualization (lesson 10) | `Visualization` subclass: `meta = VisualizationMetadata(code="KPI_CARD.X", category=VisualizationCategory.KPI_CARD, description=)`, `_render(widget, *, context) -> PresentationModel`. `Renderer` subclass: `meta = RendererMetadata(code=, description=)`, `render(model, *, context) -> RenderedOutput`. `RenderingPipeline(registry=REGISTRY, renderers=RENDERERS).render(widget, context=, renderer_code=)`. `Widget(code=, visualization_code=, binding={})`. | `examples/visualization/01_single_widget_render.py`; lesson 10 |

### APIs still to verify (next sessions)

- ~~`analytics` (lesson 07)~~ - **verified & locked**; see the analytics rows in the table above.
- ~~`decision` (lesson 08)~~ - **verified & locked**; see the decision rows above.
- ~~`digital_twin` (lesson 09)~~ - **verified & locked**; see the twin rows above.
- ~~`visualization` (lesson 10)~~ - **verified & locked**; see the visualization row above.

---

## Checkpoint

**Session ended:** context limit reached after completing **all ten lessons**
(a major milestone boundary: the entire implementation half of Milestone 1).
No work is half-finished; everything below is validated.

### Completed this session

- **Lesson 08 - Decision** authored, validated, **LOCKED**.
- **Lesson 09 - Digital Twin** authored, validated, **LOCKED**.
- **Lesson 10 - Visualization** authored, validated, **LOCKED**.
- **ALL 10 LESSONS NOW COMPLETE AND LOCKED.**
- Full sweep: `ruff` clean, `ruff format --check` clean (10 files),
  `mypy --strict` clean (10 files), **10/10 execute exit 0**.
- `src/` confirmed unmodified - no production code touched, no defect found.
- Verified-API table extended with the decision + digital_twin surfaces.

### Certification correction phase (Class A only)

Three Class A findings from the Master Certification Report were corrected.
Class B/C were explicitly **not** implemented (recorded as future work).

| ID | Finding | Correction applied | Lessons |
|---|---|---|---|
| **A1** | `CAT 793F` paired with `rated_capacity=363.0` - 363 t is the **797F**'s payload; a 793F is ~226 t. Verified against `examples/ontology/01`, which correctly pairs 797F ↔ 363.0. | Standardised on **793F @ 226 t**. Chosen over 797F @ 363 t because every lesson already uses 220 t loads - a well-loaded 793F (**97.3%**) but a badly under-loaded 797F (60.6%). Overload example 400 → 245 t (a plausible ~8% overload, not an absurd 77%). | 03, 05 |
| **A2** | One truck moving 220 t across a full 12 h shift = **18.33 t/h** - arithmetically right, operationally a broken truck, and the **first number a learner sees**. | Replaced with a realistic shift: **40 cycles × 220 t @ 0.3 h = 8,800 t over 12 h → 733.33 t/h (n=40)**. Preserves the educational objective and `n=40` now teaches provenance *better*. Identical figure in L06 also corrected. | 01, 06 |
| **A3** | Lessons taught **private** framework API: `LinearTrendModel()._analyze()`, `twin._apply()`, `ShiftKpiCard()._render()`. | Replaced with public contracts, each verified first: `.analyze()` + `isinstance` narrowing to `TrendResult`; `TwinSynchronizer.synchronize()` for cold start; a second registered renderer observing the model via `RenderingPipeline.render()`. Grep sweep confirms **zero** private framework calls remain. | 07, 08, 09, 10 |

**A3 design note (recorded, not a defect):** `Visualization` exposes **no public
method at all** - only `_render`. The only public path is
`RenderingPipeline.render()`, returning a `RenderedOutput`, not a
`PresentationModel`. There is no public way to fetch a model directly; the
pipeline *is* the contract. Class definitions overriding `_apply`/`_render`
remain in lessons 09/10 - that is the extension point you implement, which A3
explicitly permits.

**Post-correction validation:** ruff clean · `ruff format --check` 725 files ·
`mypy --strict` clean (314 src + 10 lessons) · **10/10 lessons exit 0** ·
`mkdocs build --strict` 0 warnings · `check_docs.py` 0 broken / 0 failed ·
**pytest 2,986 passed** · `src/` untouched.

**Tutorials updated for changed output:** 01 (§3/§4, code excerpt, stale 18.33
prose), 03 (§3/§5, explanation, common-mistakes), 05 (§1), 06 (§2), 07 (excerpt
→ public API), 09 (§2 cold-start), 10 (§4).

### Remaining recommendations (NOT implemented - future work)

**Class B (this milestone, when scheduled):** pytest test executing all 10
lessons (E2) · exercise solutions (D1) · surface Fundamentals on landing page +
Next Steps (U1) · exclude `LEARNING_PROGRESS.md` from the published site (U2/U3)
· name deferred packages in lesson 10 (D2) · automate expected-output
verification (E3).

**Class C (future milestone):** shared fixtures (E4) · time/difficulty markers
(D3) · lesson-length ramp (D4) · ROM pad scale (M4) · footer nav (U4).

**New finding (out of scope, recorded):** the root `README.md` and
`docs/getting-started/quick-start.md` still show the same operationally
implausible `220 t / 12 h → 18.33 t/h` example that A2 corrected in the Learning
Suite. Those are production docs outside this milestone; correcting them was not
authorised here.

### QA findings - tutorial phase

- **Lesson 04 defect found and FIXED (locked lesson revisited under the
  genuine-defect rule).** Its "time travel" section printed
  `as of 06:18 ... 875t` while the *previous* section already showed
  `875t across 4 cycles` - the same number twice. The AsOf query ran *before*
  the correction was appended, so the demo **failed to demonstrate its own
  claim**: a reader learned nothing about point-in-time replay. Execution was
  correct; the *pedagogy* was broken. Fixed by adding section 7, which re-runs
  the same AsOf query *after* the correction: `as of 06:18 = 875t (unchanged)`
  vs `as of now = 1103t across 5 cycles`. Re-validated: ruff/format/mypy clean,
  exit 0. This is exactly the class of defect that only surfaces when you write
  the tutorial and have to explain the output.

### QA findings - lesson phase

- **Lesson 09: two `mypy --strict` errors caught before locking.**
  (1) `PredicateSpecification` needed an explicit type parameter when bound to
  a bare variable: `only_our_trucks: PredicateSpecification[EventEnvelope[Any]]`.
  (2) `AsOf.utc` is `datetime | None`, so `.isoformat()` needed a narrowing
  assert. Both fixed; the strict gate did its job.
- **No production defects found.** Lessons 08-10 used the decision,
  digital_twin, and visualization APIs exactly as documented; every behaviour
  matched the specification. `src/` untouched.
- Earlier finding retained: **trend slope is per SECOND** (see the API table) -
  lesson 07 exited 0 while printing a meaningless `-0.00`. Exit 0 is not
  correctness.

### Exact next step

Implementation is **done**. The next block is **Tutorials 01-10** in
`docs/tutorials/fundamentals/` (`01_hello.md` … `10_visualization.md`).

Author them **in order, 2-3 per session**, each using the roadmap's fixed
eleven-section format (Title · Objective · Prerequisites · Concepts covered ·
Complete runnable example · Expected output · Explanation · Best practices ·
Common mistakes · Exercises · Suggested next lesson).

**Method for each tutorial:**

1. **Run the lesson first and paste its REAL output** into "Expected output".
   Never write expected output from memory - the roadmap forbids it, and
   lesson 07 proved output can be wrong even at exit 0.
2. **Embed the runnable example** by reference: link the script on GitHub
   (`https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/<dir>/<file>.py`)
   and show the key excerpt inline. Do **not** duplicate the whole script -
   reuse policy.
3. **"Common mistakes" is where the QA findings pay off.** Mine the verified-API
   table above: `eq=False` on entities (02), `RelationshipKind.BELONGS_TO` not
   `PART_OF` (05), the RATIO guardrail (06), the per-second slope trap (07),
   `AsOf.utc` being optional (09), qualify-don't-coerce (10).
4. **Cross-link** per the roadmap: script, API Reference, Architecture Handbook
   section, and next lesson.
5. Mark each tutorial row ☑ above as it lands.

**Then, in order:**
- Navigation: add a `Fundamentals` section under Tutorials in `mkdocs.yml`;
  link it from `docs/tutorials/index.md`.
- `mkdocs build --strict` (must be 0 warnings - note the link-rewrite hook at
  `scripts/docs/link_rewrite_hook.py` handles links escaping `docs/`).
- `scripts/quality/check_docs.py` (0 broken links, 0 failed snippets).
- Full `pytest` (regression check only - no production code was touched).
- Then **Phases 2-7**: freeze, and run the four independent reviews
  (Engineering QA, Educational, Mining Domain, Documentation/UX), classifying
  every recommendation as (a) defect-before-certification, (b) enhancement for
  this milestone, or (c) future-milestone candidate. Finally the Master
  Certification Report.

### Known risks / lessons learned

- **APIs are not guessable.** Lesson 05 failed on invented
  `Mine(commodity_code=…)` / `RelationshipKind.PART_OF`. Lesson 06 wrongly
  assumed `combine_results(RATIO)` returns a weighted mean - it *raises*.
  Read the source or an existing example **before** writing, every time.
- **Exit 0 is not correctness.** Lesson 07 exited 0 while printing a
  meaningless slope. Always read the numbers and ask whether they can be true.
- **The framework is often stricter than expected** - and that strictness is
  usually the best teaching material in the lesson (RATIO guardrail, slope
  units, interface-only forecasting).
- Tutorials (0/10) are the largest remaining block. Each needs all eleven
  sections, and its "Expected output" must be pasted from a **real run**, not
  imagined.
