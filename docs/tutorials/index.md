# Tutorials

Every tutorial is backed by **runnable, self-contained example scripts** in the repository - read them, then run them. Each page below reuses that example set's own guide.

!!! info "Running any tutorial"
    ```bash
    pip install -e ".[analytics]"   # analytics extra covers every example
    python examples/<topic>/<script>.py
    ```
    Each script exits `0` and prints its own output; there is nothing to configure.

## Start here - Fundamentals

**New to MineProductivity? Start with the Learning Suite.** Ten lessons that teach the platform from first principles, in the order the architecture itself is layered, using real mining problems - haul trucks, shovels, ROM stockpiles, shifts, OEE. Each lesson is a runnable script plus a full tutorial.

| # | Lesson | You will learn |
|---|---|---|
| [01](fundamentals/01_hello.md) | Hello MineProductivity | A KPI is a governed object you look up, not a formula you retype |
| [02](fundamentals/02_entities.md) | Entities | HT-214 is still HT-214 after it is refuelled and rebuilt |
| [03](fundamentals/03_value_objects.md) | Value objects | An ore grade has no identity - and cannot exist invalid |
| [04](fundamentals/04_events.md) | Events | Append-only facts, and why last June's report still reconciles |
| [05](fundamentals/05_ontology.md) | Ontology | Why two sites can't compare TPH without a shared vocabulary |
| [06](fundamentals/06_kpis.md) | KPIs | The guardrail that stops you averaging a ratio (1,200 vs 1,233.3 t/h) |
| [07](fundamentals/07_analytics.md) | Analytics | Characterise a drifting fleet without re-deriving anything |
| [08](fundamentals/08_decision.md) | Decision | Explained, audited recommendations from a versioned policy |
| [09](fundamentals/09_digital_twin.md) | Digital Twin | Live state that is always a projection of the log |
| [10](fundamentals/10_visualization.md) | Visualization | Show a human - without the layer knowing what a tonne is |

The suite's plan and progress live in the [Learning Roadmap](../learning/LEARNING_ROADMAP.md) and [Learning Progress](../learning/LEARNING_PROGRESS.md).

---

## Package Tutorials (Milestone 2)

**Deep, per-package tutorials** - the full public API, integration with the layers
below, and the extension point you implement. Each builds directly on the
Fundamentals lesson of the same package and reuses that package's runnable example
scripts.

- [01 · Core (deep)](packages/01_core.md) - the full `core` surface: identity vs
  value at depth, the four extension contracts, factory/builder, `Result`/`Maybe`,
  and implementing `BaseRepository` yourself.
- [02 · Ontology (deep)](packages/02_ontology.md) - the ten sub-ontology families
  and their spine: `BaseEntityType`, the type registry, `Relationship`s, the
  knowledge-graph projection, `OntologyValidator`, and adding an equipment leaf
  with `@register_equipment`.
- [03 · Events (deep)](packages/03_events.md) - the append-only system of record:
  canonical events, the `EventEnvelope` three-timestamp model, corrections &
  idempotency, replay/snapshots, confidence scoring, and defining a new event type.
- [04 · Registry & Plugins (deep)](packages/04_registry_and_plugins.md) - the
  extensibility subsystem: the generic `Registry` + `@register`, entry-point
  discovery, version gating, the `PluginManifest` lifecycle, activation ordering,
  and developing a custom plugin end to end.
- [05 · Connectors (deep)](packages/05_connectors.md) - the vendor-neutral
  ingestion boundary: the `FMSConnector` contract, the `CONNECTORS` registry,
  resilient network ingestion (retry/auth), normalization, and implementing a
  connector for a new source. **Completes Unit A (Foundation).**
- [06 · KPIs (deep)](packages/06_kpis.md) - **opens Unit B (Intelligence):** the
  metadata-first metric backbone — the `KPIEngine` over an event store, composite
  KPIs and the dependency graph, the 29-field governed metadata, discovery, and
  defining a new KPI.
- [07 · Analytics (deep)](packages/07_analytics.md) - characterising KPI history
  without re-deriving it: the statistical surface, `LinearTrendModel`, the
  model-as-object families, and implementing the interface-only `ForecastingModel`.
- [08 · Decision (deep)](packages/08_decision.md) - explained, audited
  recommendations from a versioned `Policy`: rules vs thresholds, the pipeline
  stages, ranking/planning, real-time sessions, a strategy plugin, and the
  root-cause/what-if refusal.

- [09 · Digital Twin (deep)](packages/09_digital_twin.md) - live state that is always a projection of the event log: `_apply`-only evolution, cold-start replay, live sync, snapshots, and a custom `Twin` plugin.

- [10 · Simulation (deep)](packages/10_simulation.md) - hypothetical futures over a governed `Scenario`, seeded from a twin snapshot: Monte-Carlo experiments, scenario comparison, sensitivity sweeps, statistics delegated to analytics, and a model plugin.

- [11 · Optimization (deep)](packages/11_optimization.md) - the best feasible plan over a governed `OptimizationProblem`: MIP fleet allocation, plan comparison, sensitivity, candidate search over simulation, and a solver-adapter plugin.

- [12 · AI Agents (deep)](packages/12_agents.md) - model-independent orchestration: governed tasks, policy-gated approval, tools composing simulation/optimization, multi-agent workflows, and a plugin agent+tool.

- [13 · Visualization (deep)](packages/13_visualization.md) - presenting governed evidence to a human without a charting-library dependency: the `PresentationModel`, the one `RenderingPipeline`, dashboards/reports/export, and a visualization+renderer plugin.

**✅ All 13 Package Tutorials are complete.**

---

The sections below are **per-package API walkthroughs** - lighter capability tours of each package's API, complementing the Fundamentals path and the deep Package Tutorials above.

## Foundation

- [Quick tour](quickstart.md) - the five-minute, whole-platform script.
- [Core](core.md) - entities, value objects, repositories, factories/builders, validation, serialization.
- [Events](events.md) - first event, replay/time-travel, corrections.
- [Ontology](ontology.md) - equipment modelling, structural modelling, contextual validation.
- [Registry](registry.md) - the register → discover → lookup mechanism every plugin shares.
- [Connectors](connectors.md) - CSV ingestion, REST with retry/auth-refresh.
- [KPIs](kpis.md) - single-KPI execution, composite `UTIL.OEE`, batch summary, discovery.

## Intelligence

- [Decision](decision.md) - audited pipelines, action prioritization, real-time sessions, plugin strategies.
- [Digital Twin](digital_twin.md) - cold-start + live synchronization, discovery, snapshots, plugin twin types.
- [Simulation](simulation.md) - snapshot-seeded Monte Carlo, scenario comparison, sensitivity sweeps.
- [Optimization](optimization.md) - MIP fleet allocation, plan comparison, sensitivity, candidate search, plugin solvers.
- [AI Agents](agents.md) - single tasks, policy-gated approval, multi-agent workflows, plugin agents/tools.
- [Visualization](visualization.md) - single-widget render, multi-source dashboards, exported reports, plugins.
