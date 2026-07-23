# Milestone 2 - Package Tutorials: Architecture

> **Status: Architecture (design only).** No lessons, tutorials, or code have
> been written. This document is the design contract for Milestone 2, built on
> the LOCKED [`LEARNING_ROADMAP.md`](../LEARNING_ROADMAP.md) and the standards
> proven in Milestone 1. It is versioned with the Suite, not with the framework.

## 0. How Milestone 2 differs from Milestone 1

Milestone 1 (Fundamentals) taught **eight packages at intro depth** - one
central concept each, in layer order, as one continuous story. Milestone 2
teaches **depth per package**: the full public API surface, integration with the
layers below, and - crucially - the **extension point** each package exposes.

| | Milestone 1 (Fundamentals) | Milestone 2 (Package Tutorials) |
|---|---|---|
| Unit of teaching | one *concept* per package | one *package* in full |
| Depth | the single idea that unlocks the layer | the public API, integration, and extension |
| Packages | 8 (intro) | 14 packages in 13 tutorials - 6 packages (5 tutorials) new to the Suite |
| Capstone theme | "the chain, end to end" | **"write a plugin"** - delivering on every M1 refusal |
| Prerequisite | none (first contact) | the matching M1 lesson, where one exists |

The teaching **philosophy and audience model are inherited unchanged** from the
Learning Roadmap (§3, §2). The **tutorial format is deliberately richer** than
M1's intro-lesson layout: Package Tutorials use the **16-section Package Tutorial
Template v1.0** (§11), which extends M1's structure with the depth-specific
sections (architectural role, integration, package structure, public-API surface
under a coverage convention, performance, extension points, reference solutions).
Template v1.0 was validated against Tutorial 1 (Core) and independently reviewed
before adoption.

## 1. Package coverage & grouping

The Learning Roadmap's M2 scope **originally named 11 domain packages**
(`core, ontology, events, kpis, analytics, decision, digital_twin, simulation,
optimization, agents, visualization`); Decision D1 expanded it to **14** and the
roadmap is now synchronized (see below).

**Grouping (not a source-tree mirror):** all 14 fall naturally into the
architecture's own two tiers, which is also the correct *learning* order because
a package tutorial may assume every layer beneath it.

### Roadmap amendment (scope APPROVED — Decision D1; roadmap SYNCHRONIZED 2026-07-18)

The roadmap's M2 list **omits the three cross-cutting packages** `registry`,
`plugins`, `connectors`. Designing M2 surfaced this as a **genuine coverage
gap**, not a preference:

- **`registry` + `plugins`** are the *mechanism* behind every "write a plugin"
  refusal in Milestone 1 (analytics forecasting, decision root-cause,
  optimization solvers, agent backends, renderers). A "Package Tutorials"
  milestone that never teaches them leaves a learner who finished the **entire
  Suite** still unable to author a plugin - the platform's headline extension
  model. The M2 plugin-authoring content (§4, woven) *depends* on them.
- **`connectors`** is the ingestion boundary. Every lesson to date used
  in-memory stores or hand-built events; a practitioner needs `connectors` to
  get real FMS/dispatch data into the platform. It is a package, and M2 is
  "Package Tutorials".

**Decision D1 (APPROVED):** Option A adopted — the roadmap's M2 scope gains
`registry`/`plugins` (as one combined unit) and `connectors`, giving **13
package tutorials over 14 packages**. The `LEARNING_ROADMAP.md` M2-scope line was
**synchronized on 2026-07-18** (11 → 14 packages, recorded in the roadmap's
Revision History); only that one scope cell changed. The 11 originally
roadmap-mandated tutorials are marked **[core]** and the two added by D1 are
marked **[+D1]**.

### The two learning units

**Unit A - Foundation, at depth** (the substrate; mostly introduced in M1):

| Order | Tutorial | Pkgs | API | M1 intro? | Scope |
|---|---|---|---|---|---|
| 1 | Core | `core` | 38 | ✔ (L02/03) | [core] |
| 2 | Ontology | `ontology` | 56 | ✔ (L05) | [core] |
| 3 | Events | `events` | 31 | ✔ (L04) | [core] |
| 4 | Registry & Plugins | `registry`+`plugins` | 11+8 | ✘ | [+D1] |
| 5 | Connectors | `connectors` | 25 | ✘ | [+D1] |
| 6 | KPIs | `kpis` | 32 | ✔ (L01/06) | [core] |

**Unit B - Intelligence, at depth** (layer order; includes the three M1 never covered):

| Order | Tutorial | Pkg | API | M1 intro? | Scope |
|---|---|---|---|---|---|
| 7 | Analytics | `analytics` | 53 | ✔ (L07) | [core] |
| 8 | Decision | `decision` | 49 | ✔ (L08) | [core] |
| 9 | Digital Twin | `digital_twin` | 36 | ✔ (L09) | [core] |
| 10 | Simulation | `simulation` | 34 | ✘ **new** | [core] |
| 11 | Optimization | `optimization` | 36 | ✘ **new** | [core] |
| 12 | AI Agents | `agents` | 41 | ✘ **new** | [core] |
| 13 | Visualization | `visualization` | 29 | ✔ (L10) | [core] |

## 2. Dependency graph (learning prerequisites)

A learner may take an M2 tutorial once they have (a) the matching M1 lesson and
(b) the M2 tutorials of the packages it *imports*. Arrows = "should be taken
before".

```
M1 Fundamentals (all 10)  ─┐   (recommended baseline for the whole of M2)
                           │
Unit A:  Core ─► Ontology ─► Events ─► Registry&Plugins ─► Connectors ─► KPIs
                                          │  (Connectors produces Events;
                                          │   KPIs consumes Events)
Unit B:  KPIs ─► Analytics ─► Decision ─► Digital Twin ─► Simulation
                                                   └─► Optimization ─► Agents ─► Visualization
```

- **Registry & Plugins is deliberately early** (position 4): it is small,
  foundational, and every later "how to extend" section references it.
  **Prerequisite note (mechanism-before-motivation):** teaching the plugin
  *mechanism* at position 4 - before Unit B's interface-only packages *motivate*
  it - is sound **only because Milestone 1 is a hard prerequisite for M2**. M1
  already established the refusals (analytics ships no forecaster, decision no
  root-cause engine, visualization no renderer), so a learner reaching position 4
  has *felt the "why"* even though M2's own interface-only tutorials come later.
  Absent the M1 baseline this ordering would be premature; with it, it is correct.
- **Connectors follows Events** (it *produces* events) and precedes KPIs (which
  consume them from a store a connector filled).
- **Intelligence order mirrors the locked dependency chain** exactly, so no
  tutorial meets a type before its home tutorial.

## 3. Per-package design

Each row is the tutorial's contract. **APIs to teach = public surface only**
(the package `__all__`); private methods are shown *only* where the lesson
explicitly explains an extension point you implement (e.g. `_solve_lp`), per the
M1 A3 correction. **Reuse** lists existing example scripts to build on.

### Unit A

**1 · Core** - Beginner→Intermediate · ~60 min · reuse: `examples/core/` (6)
- **Why it exists / problem:** the primitives every other package reuses so the
  platform has one entity model, one repository contract, one error style.
- **Teach:** `BaseEntity`/`BaseValueObject` (depth beyond M1), `BaseRepository`
  + `InMemoryRepository`, `BaseSpecification`/`PredicateSpecification`,
  `BaseBuilder`/`BaseFactory`, `Result`/`Maybe`, serialization, identifiers.
- **Extension point:** implement `BaseRepository[E, str]` (a production backend)
  - the one every `*Repository` type alias resolves to.
- **Integrates with M1:** deepens L02 (entities) and L03 (value objects).
- **Common mistakes:** `eq=False` on entities; mutating frozen objects; using an
  entity where a value object belongs; `Result` unwrap without `is_ok`.

**2 · Ontology** - Intermediate→Advanced · ~90 min (largest API) · reuse: `examples/ontology/` (3)
- **Why:** the shared vocabulary that makes a tonne mean the same at two pits.
- **Teach:** the ten sub-ontology families (equipment, material, location, org,
  production, maintenance, cost, quality, safety, environmental), the equipment
  inheritance split, `Relationship`/`RelationshipKind`, `Shift`/`ShiftCalendar`,
  `KnowledgeGraphProjection`, contextual validation, `to_schema()`.
- **Extension point:** `register_equipment` (a custom leaf type); a custom
  `KnowledgeGraphProjection`.
- **Integrates with M1:** deepens L05.
- **Common mistakes:** `commodity_codes` (plural) not `commodity_code`;
  `RelationshipKind.BELONGS_TO` not `PART_OF`; nesting entities vs edges.

**3 · Events** - Intermediate · ~60 min · reuse: `examples/events/` (3)
- **Why:** the immutable system of record everything projects from.
- **Teach:** the canonical event families, `EventEnvelope`/three timestamps,
  `EventStore`/`EventBus`, `EventQuery`, `AsOf`/`replay`, codecs (Arrow/Parquet),
  idempotency, `EventValidator` confidence.
- **Extension point:** a custom codec; a custom `EventStore`/`EventBus` backend.
- **Integrates with M1:** deepens L04.
- **Common mistakes:** editing a fact; ingestion-time-as-event-time; tz-less
  datetimes; dropping "bad" data instead of scoring confidence.

**4 · Registry & Plugins** [+D1] - Intermediate · ~45 min · reuse: `examples/registry/` (2); **plugins has NO examples - new needed**
- **Why:** the plugin-first mechanism every domain package specialises; the
  answer to every M1 "write a plugin".
- **Teach:** `Registry`/`register`, `EntryPointDiscovery`/`EntryPointSpec`,
  plugin manifests/states/activation ordering, the register→discover→activate
  lifecycle, the three-way distinction (registry=types, repository=instances,
  discovery=query facade).
- **Extension point:** *this is the extension point* - an entry-point plugin.
- **Integrates:** underpins every later "how to extend" section.
- **Common mistakes:** conflating registry/repository/discovery; expecting a
  duplicate registration to be silently accepted (it raises).

**5 · Connectors** [+D1] - Intermediate · ~45 min · reuse: `examples/connectors/` (2)
- **Why:** the vendor-neutral ingestion boundary - how real data becomes events.
- **Teach:** the `FMSConnector` contract, reference connectors (CSV/Excel/REST/
  GraphQL/Kafka/MQTT), `RetryPolicy`, auth refresh, OEM adapter shapes.
- **Extension point:** implement `FMSConnector` for a real source system.
- **Integrates:** feeds the `EventStore` that KPIs (Unit A) consume.
- **Common mistakes:** connectors is the *only* domain-adjacent package above
  `events` that intentionally uses `connectors`-style retry - do not re-invent
  retry; ingest to events, do not compute KPIs in a connector.

**6 · KPIs** - Intermediate→Advanced · ~75 min · reuse: `examples/kpis/` (5)
- **Why:** the metadata-first metric backbone.
- **Teach:** the **`KPIEngine` over an event store** (the path M1 L06 deferred),
  `BaseKPI`/`CompositeKPI`, `DependencyGraph`, `KPIMetadata` (29 fields),
  `Aggregation` + the RATIO guardrail, execution backends (numpy/pandas/polars/
  duckdb), `ResultCache`, the 12-KPI Standard Library.
- **Extension point:** a custom `BaseKPI`/`CompositeKPI`; a custom
  `ExecutionBackend`.
- **Integrates with M1:** deepens L01/L06; connects to Connectors (data in) and
  Events (facts).
- **Common mistakes:** averaging a ratio (re-derive from raw rows); importing
  `combine_results` from the top level; calling `.compute()` on a composite.

### Unit B

**7 · Analytics** - Advanced · ~90 min · reuse: **NONE - `examples/analytics/` does not exist (see Risks)**
- **Why:** characterise governed facts without re-deriving them.
- **Teach:** the full statistical surface (`describe`/percentile/histogram/
  distribution/confidence_interval), rolling/trend/baseline/benchmark, the
  pipeline (`AnalyticsPipeline`/stages), batch/streaming/incremental runners,
  data-quality scoring, the interface-only forecasting/anomaly/outlier ABCs.
- **Extension point:** implement `ForecastingModel`/`AnomalyDetector`/
  `OutlierDetector` as a plugin.
- **Common mistakes:** re-deriving a KPI inside analytics; the **per-second
  slope** unit trap; trusting `direction` without `r_squared`; expecting a
  built-in forecaster.

**8 · Decision** - Advanced · ~90 min · reuse: `examples/decision/` (5)
- **Why:** translate statistical judgement into explained, audited action.
- **Teach:** `DecisionPipeline`/stages, `Rule`/`RuleEngine`, `Policy` governance,
  `ThresholdDecisionStrategy`, scoring/`RankingStrategy`, `ExplanationBuilder`,
  `ActionPrioritizer`/`ActionPlanner`, `AlertGenerator`, real-time/batch
  runners, `DecisionAuditTrail`, the interface-only `RootCauseAnalyzer`/
  `WhatIfEngine`.
- **Extension point:** a custom `DecisionStrategy`/`Rule`; a `RootCauseAnalyzer`
  plugin.
- **Common mistakes:** business rules as inline `if`s; re-deriving evidence;
  rules without thresholds; skipping the `ExplanationStage`.

**9 · Digital Twin** - Advanced · ~75 min · reuse: `examples/digital_twin/` (4)
- **Why:** stateful representation that is always a projection of the log.
- **Teach:** the 11 category bases, `Twin` lifecycle, `TwinSynchronizer`/
  `SyncPolicy`, `TwinState`/`TwinSnapshot`, `TelemetryReading`, cold-start
  replay, discovery, the interface-only `TwinSimulationModel`.
- **Extension point:** a custom `Twin` subclass; a `TwinSimulationModel` plugin.
- **Common mistakes:** adding a setter; persisting twin state as source of
  truth; `AsOf.utc` narrowing; use the public `TwinSynchronizer`, not `_apply`.

**10 · Simulation** - Advanced · ~75 min · **first exposure** · reuse: `examples/simulation/` (4)
- **Why:** the projection layer - hypothetical futures over a governed scenario.
- **Teach:** `Scenario`/`ScenarioStatus` governance, `SimulationRun`/
  `SimulationExecutor`, `SimulationClock`/`TimeProgressionMode`,
  `seed_from_replay`, the four interface-only methodology ABCs (Monte Carlo/
  discrete-event/system-dynamics/calibration), `ExperimentRunner`,
  `ScenarioComparator`/`SensitivityAnalyzer` (delegating to analytics),
  `SimulationStateCache`.
- **Extension point:** a `MonteCarloModel` (etc.) plugin.
- **Common mistakes:** stateful RNG across trials (seed everything); expecting a
  shipped simulation model; re-implementing statistics instead of delegating.

**11 · Optimization** - Advanced · ~75 min · **first exposure** · reuse: `examples/optimization/` (5)
- **Why:** the prescriptive-search layer - the best feasible plan.
- **Teach:** `OptimizationProblem` governance, the six interface-only paradigm
  ABCs (LP/MIP/CP/multi-objective/evolutionary/network), `OptimizationExecutor`
  category dispatch, `PlanComparator`/`SensitivityAnalyzer`, candidate-scenario
  search over `simulation.ExperimentRunner`.
- **Extension point:** a solver adapter (subclass a paradigm ABC + `@register`);
  the platform imports **no** solver library.
- **Common mistakes:** expecting a shipped solver; mixing non-continuous
  variables with an LP category; re-deriving statistics.

**12 · AI Agents** - Advanced · ~90 min · **first exposure** · reuse: `examples/agents/` (5)
- **Why:** model-independent orchestration of autonomous work.
- **Teach:** interface-only `Agent`/`Tool`/`AgentMemory`, `Task` lifecycle +
  `AwaitingApproval`, `TaskExecutor` (gate→dispatch→retry→persist→audit) +
  `resume()`, `PolicyEngine`/`AgentPolicy`/capabilities, `WorkflowEngine`
  delegation (composing simulation/optimization), `AgentAuditTrail`, the dual
  `REGISTRY`/`TOOLS` registries.
- **Extension point:** a reasoning-backend `Agent`, a `Tool`, an `AgentMemory` -
  LLM SDKs live in the plugin, never the package.
- **Common mistakes:** expecting a built-in agent; the executor never resolves an
  approval (the caller supplies a resolved `ApprovalRequest`); unscoped Active
  deny policies gating everything.

**13 · Visualization** - Intermediate→Advanced · ~60 min · reuse: `examples/visualization/` (5)
- **Why:** present already-governed evidence to a human; the final package.
- **Teach:** interface-only `Visualization`/`Renderer`, `PresentationModel`
  (no bytes), `Widget`/`Dashboard`/`Layout`/`Theme`, `DashboardBuilder`/
  `ReportBuilder`, the single `RenderingPipeline`, `Report`/export, dual
  `REGISTRY`/`RENDERERS`.
- **Extension point:** a `Visualization` + a `Renderer` plugin (charting library
  lives in the plugin).
- **Integrates with M1:** deepens L10.
- **Common mistakes:** computing in a visualization; defaulting missing data to
  `0.0`; putting bytes/colours in `PresentationModel`; `Visualization` has no
  public method - observe a model via a renderer, not `_render`.

## 4. Plugin authoring - woven, not bolted on

Rather than a separate capstone unit, **every package tutorial with an extension
point ends with a "How to extend this package" section** that authors a real
plugin, reusing the existing plugin examples. Two kinds of extension point
appear: *interface-only* packages (ship an abstract contract with **zero**
implementations - you must supply one) and *concrete-with-a-seam* packages (ship
working defaults **and** an overridable base - you add your own alongside).

| Package | Extension kind | Plugin authored | Reuse asset |
|---|---|---|---|
| analytics | interface-only | forecasting model | **new (no example exists)** |
| decision | interface-only | decision strategy | `examples/decision/04_plugin_strategy.py` |
| digital_twin | interface-only | custom twin type | `examples/digital_twin/04_plugin_twin_type.py` |
| simulation | interface-only | Monte-Carlo / methodology model | `examples/simulation/04_plugin_simulation_model.py` |
| optimization | interface-only | solver adapter | `examples/optimization/05_plugin_solver_adapter.py` |
| agents | interface-only | agent + tool | `examples/agents/05_plugin_agent_and_tool.py` |
| visualization | interface-only | visualization + renderer | `examples/visualization/05_plugin_visualization_and_renderer.py` |
| registry & plugins | *is the mechanism* | entry-point plugin | `examples/registry/` (2); plugins **new** |
| kpis | concrete-with-a-seam | custom `BaseKPI` / `ExecutionBackend` | `examples/kpis/` (5) |
| connectors | concrete-with-a-seam | custom `FMSConnector` | `examples/connectors/` (2) |

This makes Milestone 2 the payoff for every Milestone 1 refusal, without a
thirteen-then-three structure, and keeps "depth per package" intact. Seven of the
thirteen tutorials are interface-only; `registry & plugins` teaches the mechanism
itself; `kpis`/`connectors` extend a concrete base.

## 5. Learning outcomes

On completing Milestone 2 a reader can, for **any** package:

1. State *why* the package exists and what problem it solves (why-before-how).
2. Use its **full public API** correctly, from realistic mining inputs.
3. Explain how it integrates with the layers below and consumes their governed
   outputs without re-deriving them.
4. Identify and **author a plugin** against its interface-only extension point.
5. Recognise its common failure modes and the framework guardrails that catch
   them.
6. Place it precisely in the locked dependency chain.

Milestone-level outcome: a practitioner who has finished M1 + M2 can **extend
MineProductivity**, not merely use it - the plugin-first architecture is now
teachable end to end.

## 6. Exercise strategy

Inherit M1's style (4–5 exercises per tutorial, graded easy→open-ended), plus
two M2-specific additions justified by the depth jump:

- **A "build a plugin" exercise in every interface-only tutorial** - the
  learner authors a minimal concrete subclass and registers it. This is the
  single most valuable exercise class in M2.
- **A cross-package integration exercise** per Unit B tutorial - wire the
  package to the one below (e.g. feed a `TrendResult` into a `Decision`
  `Policy`), reinforcing "consume, never re-derive".
- **Address M1 gap D1:** M2 should ship **exercise solutions/hints** from the
  start (M1 deferred these). Recommended: a collapsed `??? note "Solution"`
  admonition per exercise.

## 7. Validation approach (inherited from M1, extended)

Per-tutorial, before LOCK - identical gates to M1:
`ruff` · `ruff format --check` · `mypy --strict` · execute the script (exit 0) ·
paste **real** output into "Expected output" · verification-first authoring
(read the implementation before writing).

Milestone-level: `mkdocs build --strict` (0 warnings) · `check_docs.py`
(0 broken, 0 failed) · full `pytest` (no regression) · `src/` untouched unless a
genuine defect.

**New for M2 - automated lesson-execution test (closes M1's top Class-B item,
E2):** add a `pytest` case that imports/executes every M1 and M2 lesson script
and asserts exit 0. Without it, a growing corpus of lessons is protected only by
manual validation and will rot. **This is the highest-leverage validation
investment in M2** and should land early, retrofitting M1's ten lessons too.

## 8. Estimated milestone size

| Metric | Estimate |
|---|---|
| Package tutorials | **13 tutorials over 14 packages** (11 [core] + 2 [+D1] - all approved under Option A) |
| New example scripts required | **~6–10** - analytics (no dir), plugins (no dir), plus deeper KPIEngine/connector scripts; most other packages reuse existing demos |
| Tutorial pages | 13 (Package Tutorial Template v1.0, 16 sections — §11) |
| Est. authoring effort | **3–4× Milestone 1** (depth + 5 never-taught packages + larger APIs). Ontology/analytics/decision/agents are the long poles. |
| Suggested phasing (resumable) | **M2a** = Unit A (6 tutorials) · **M2b** = Unit B (7 tutorials). Checkpoint between phases. |

**Checkpoint cadence (inherited from M1, made explicit).** The unit-level
M2a/M2b split is the *coarse* phase boundary; the *operative* checkpoint unit is
the **individual tutorial**, exactly as Milestone 1 locked per-lesson. Each
tutorial is authored → validated (all §7 gates) → **LOCKED** before the next
begins, and `LEARNING_PROGRESS.md` is updated at every LOCK with the verified-API
carry-forward. This means M2 is resumable at any tutorial boundary (13 natural
resume points), not only at the M2a/M2b seam - the guard against multi-session
drift (Risk R5).

## 9. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | ~~**Scope decision** - registry/plugins/connectors omitted from the locked roadmap M2 line.~~ **RESOLVED (Decision D1):** Option A approved; scope is 13 tutorials / 14 packages. | ~~High~~ → Closed | Architecture updated. Residual: the `LEARNING_ROADMAP.md` file sync awaits a separate explicit approval of the prepared amendment text (governance gate, not a design risk). |
| R2 | **No `analytics` or `plugins` examples exist** to reuse - M2 must author them from scratch, against the M1 reuse-first rule. | Medium | Treat as an M2 dependency; the analytics gap is already a known v2.0 Recommended Improvement. Author new, verification-first. |
| R3 | **Six packages (registry, plugins, connectors, simulation, optimization, agents) had no M1 intro** - five tutorials with higher intrinsic difficulty and no "deepens L0x" scaffold. | Medium | Each such tutorial must carry its *own* why-before-how framing, not lean on an M1 lesson. |
| R4 | **Large APIs** (ontology 56, analytics 53, decision 49) may not fit one tutorial. | Medium | Allow a 2-part split *within* a package tutorial if a validated draft exceeds ~200 lines; not a format change. |
| R5 | **Milestone drift/rot** - 13 deep tutorials over many sessions. | Medium | Reuse M1's checkpoint protocol + carry-forward verified-API table (already rich); land the automated lesson test (§7) early. |
| R6 | **Private-API temptation** is higher at depth (more internals visible). | Low | The M1 A3 rule is binding: public contracts only; private methods shown only as extension points you implement. |

## 10. Definition of Done - Milestone 2

Milestone 2 is complete only when **all** hold:

**Per package tutorial**
- [ ] Script(s) exist, self-contained, **public APIs only**, realistic mining domain
- [ ] Executes to exit `0`; `ruff` / `ruff format --check` / `mypy --strict` clean
- [ ] Follows **Package Tutorial Template v1.0** (§11): all required sections
      present, coverage convention applied (every `__all__` symbol tagged
      [deep] or [ref]), "Expected output" pasted from a **real** run
- [ ] "How to extend this package" section authors a real plugin (where interface-only)
- [ ] Exercises include a build-a-plugin task **and** ship solutions/hints
- [ ] Cross-links: script · API Reference · Architecture Handbook · next tutorial

**Per milestone**
- [ ] All **13** tutorials pass (scope fixed by Decision D1)
- [ ] Automated lesson-execution `pytest` test green (covers M1 + M2)
- [ ] `mkdocs build --strict` 0 warnings · `check_docs.py` 0 broken / 0 failed
- [ ] Full `pytest` green (no regression); `src/` unmodified unless a recorded defect
- [ ] Navigation updated; a "Package Tutorials" section sits under Tutorials
- [ ] `LEARNING_PROGRESS.md` reflects true state; `LEARNING_ROADMAP.md` M2-scope
      line synced to 14 packages (once the prepared amendment is approved & applied)
- [ ] Independent reviews (as M1: Engineering, Educational, Mining, UX) + certification

## 11. Package Tutorial Template v1.0

The canonical **structure** every Package Tutorial (2–13) follows. Established by
Tutorial 1 (Core), independently reviewed, and adopted here as the standard.
Reference implementation: [`../../tutorials/packages/01_core.md`](../../tutorials/packages/01_core.md).
The **process** that produces a tutorial to this structure — verification,
validation, extension, review, lock, checkpoint — is the frozen
[Package Tutorial Implementation Standard](../PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md),
which lets Tutorials 2–13 be commissioned with only *package* + *number*.

### 11.1 Section structure (16 sections)

Front matter: milestone banner · **Objective** · **Prerequisites** (link the
matching M1 lesson + any prerequisite Package Tutorials) · **Running the examples**.

| # | Section | Required? | Notes |
|---|---|---|---|
| 1 | Why this package exists | **Required** | The problem it solves; why-before-how. |
| 2 | Architectural role | **Required** | Position in the locked chain; DIP. |
| 3 | **Integration with adjacent layers** | **Required** | How it consumes the layer(s) below **without re-deriving** them. **Tutorial 1 (Core) marks this "N/A — foundational layer"; mandatory and substantive for 2–13.** |
| 4 | Package structure | **Required** | Module map. May be abbreviated for small packages (< ~15 symbols). |
| 5 | Public APIs | **Required** | The full `__all__`, grouped by role, under the **coverage convention** (§11.4). |
| 6 | Conceptual model | **Required** | The handful of ideas that explain the package. |
| 7 | Real mining examples | **Conditional** | Full section when the package is domain-free/thin (e.g. Core); may be abbreviated to a sentence in §6/§8 when the package *is* domain (e.g. ontology, kpis). |
| 8 | Step-by-step walkthroughs | **Required** | Numbered sub-sections; each ends with **verbatim executed output**. |
| 9 | Repository example reuse | **Required** | Table: script → APIs exercised → walkthrough. New scripts only where none exist (Risk R2). |
| 10 | Common mistakes | **Required** | Verified failure modes + the fix. |
| 11 | Best practices | **Required** | |
| 12 | Performance considerations | **Conditional** | Full section where the package has real perf characteristics; may be abbreviated to 1–2 bullets otherwise. |
| 13 | Extension points | **Required** | The package's seam, taught with a runnable, gate-clean example. For interface-only packages this authors a real plugin. |
| 14 | Exercises | **Required** | 4–5, graded easy → open-ended; include one build-against-the-extension-point task. |
| 15 | Reference solutions | **Required** | Collapsed `??? success` per exercise (closes M1 gap D1). |
| 16 | Further reading | **Required** | Package guide · API reference · Architecture Handbook · the M1 lesson(s) deepened. |

Footer: **"Next package tutorial"** pointer.

### 11.2 Required vs optional / abbreviation

- **Required (always present):** 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16.
- **Conditional (present, but may be abbreviated to a short note with a one-line
  justification):** 7 (Real mining examples) and 12 (Performance).
- A section is **never dropped** — an abbreviated section still appears with its
  heading and a sentence stating why it is short (keeps all 13 tutorials
  structurally comparable). §3 uses an explicit "N/A — foundational layer" note
  for Core only.

### 11.3 Split criteria for very large packages

Author as a **single tutorial** by default. Split into a `part A / part B` pair
(same numbered structure, walkthroughs partitioned by theme) only when a
**validated draft** exceeds **either** ~700 rendered lines **or** ~40 symbols
requiring deep coverage. Likely triggers: `ontology` (56), `analytics` (53),
`decision` (49). A split is a length accommodation, **not** a format change — both
parts still satisfy this template and the Definition of Done as one unit.

### 11.4 Coverage convention

Every symbol in the package `__all__` belongs to **exactly one** category, and
**no public symbol is left undocumented**:

- **[deep]** — taught in a walkthrough (§8) with an **executed** example and
  verbatim output, or in the extension-point section (§13).
- **[ref]** — reference coverage: a one-line "what / when to reach for it" in a
  **"Reference coverage"** subsection of §5, plus the API-reference pointer.
  Reserved for cross-cutting/marker/type-alias symbols used mostly *through* other
  packages (e.g. Core's `BaseConfiguration`, `BaseService`, `Comparable`,
  `Identifiable`, `JSONValue`, `JSONPrimitive`, `ConfigurationError`, `BuilderError`).

The Definition of Done requires that the `[deep]` + `[ref]` tags partition the
entire `__all__` with none missing.

### 11.5 Non-negotiables (inherited)

Public APIs only (private shown solely as an extension point you implement);
verification-first authoring; realistic mining domain; every code block executed
and its output pasted verbatim; builds on — never repeats — the matching M1 lesson.

---

*Design authored against the LOCKED Learning Roadmap. Scope is settled by
Decision D1 (Option A: 13 tutorials / 14 packages), and the `LEARNING_ROADMAP.md`
M2-scope line is **synchronized** (2026-07-18, recorded in its Revision History).
Frozen with one approved amendment (2026-07-18): §11 **Package Tutorial Template
v1.0** added and the "eleven-section" wording updated to the 16-section template,
following the Tutorial 1 independent review. Roadmap, architecture, and progress
tracker agree.*
