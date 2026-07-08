# Architecture Documentation

## Purpose

Companion documentation for the Master Architecture Handbook v1.0 — the locked SSOT describing MineProductivity's overall system architecture, layering, and design principles.

## Scope

Architectural rationale, layering diagrams, dependency rules, and cross-cutting design decisions (Clean Architecture, DDD, event-sourcing, ontology-first modeling). Does not include package-level implementation detail — that belongs in each package's own `README.md` under `src/mineproductivity/`.

## Responsibilities

- Explain the inward-pointing dependency direction between `core`, `ontology`, `events`, `kpis`, `analytics`, `decision`, `digital_twin`, `simulation`, `optimization`, `agents`, and `visualization`.
- Document forbidden import patterns and architectural boundaries.
- Serve as the entry point for new contributors to understand system shape before reading code.

## Contents

**Foundation** (implemented):

- `01_Event_Framework_Design_Specification.md` — `events` package: `BaseEvent`, `EventEnvelope`, `EventStore`, `EventBus`, replay/time-travel, idempotency.
- `02_Ontology_Framework_Design_Specification.md` — `ontology` package: the ten sub-ontology families (equipment, material, location, organization, production, maintenance, cost, quality, safety, environmental) and the Knowledge Graph projection contract.
- `03_Registry_Framework_Design_Specification.md` — `registry` + `plugins` packages: the generic registration/discovery mechanism every domain registry (KPI, Connector, Ontology, Analytics) specializes.
- `04_Connector_Framework_Design_Specification.md` — `connectors` package: the `FMSConnector` contract, reference connectors (CSV/Excel/REST/GraphQL/Kafka/MQTT), and OEM adapter shapes (MineStar, DISPATCH, Wenco, Modular Mining, Hexagon).
- `05_KPI_Engine_Design_Specification.md` — `kpis` package: `BaseKPI`, the 29-field `KPIMetadata` schema, the dependency graph, aggregation semantics, and vectorized execution backends. The platform's most important design specification.

**Intelligence** (`analytics`, `decision`, and `digital_twin` implemented; the rest design-complete, implementation not yet started):

- `06_Analytics_Engine_Design_Specification.md` — `analytics` package: `AnalyticsModel`, forecasting/anomaly/outlier-detection interfaces (interface only), streaming and batch pipelines, statistical primitives (`describe`, `confidence_interval`) every higher package delegates to. **Implemented** on `main`; see `ADR-0006-Analytics-Engine.md` in `docs/adr/` for the decision record.
- [`07_Decision_Intelligence_Design_Specification.md`](07_Decision_Intelligence_Design_Specification.md) — `decision` package: `DecisionModel`, rule engine, root-cause/what-if interfaces (interface only), policy governance, decision audit trail. **Fully implemented** on `main` (`DecisionModel`/`DecisionContext`, rule composition/evaluation, `Policy` governance, `ThresholdDecisionStrategy`, scoring, ranking, explanation, prioritization, the interface-only `RootCauseAnalyzer`/`WhatIfEngine`, `ActionPlanner`, `AlertGenerator`, `RealTimeDecisionSession`/`BatchDecisionRunner`, and `DecisionAuditTrail`); see `ADR-0007-Decision-Intelligence.md` in `docs/adr/` for the decision record. `decision` is feature-complete per design spec §6's module list.
- [`08_Digital_Twin_Design_Specification.md`](08_Digital_Twin_Design_Specification.md) — `digital_twin` package: `Twin` (a stateful `core.BaseEntity`), synchronization, snapshots, telemetry integration, an interface-only simulation bridge (`TwinSimulationModel`). **Fully implemented** on `main` (the complete design spec §6 module list); see `ADR-0008-Digital-Twin.md` in `docs/adr/` for the decision record.
- [`09_Simulation_Design_Specification.md`](09_Simulation_Design_Specification.md) — `simulation` package: scenario management, `SimulationRun` execution, interface-only Monte Carlo/discrete-event/system-dynamics/calibration models, experiment orchestration, scenario comparison and sensitivity analysis (delegated to `analytics`).
- [`10_Optimization_Design_Specification.md`](10_Optimization_Design_Specification.md) — `optimization` package: `OptimizationModel`, six interface-only solving paradigms (linear programming, mixed-integer programming, constraint programming, multi-objective, evolutionary/metaheuristic, network optimization), `OptimizationRun` execution, plan comparison and sensitivity analysis (delegated to `analytics`).
- [`11_AI_Agents_Design_Specification.md`](11_AI_Agents_Design_Specification.md) — `agents` package: `Agent`, model-independent reasoning-backend contract, `Task` lifecycle and execution, policy engine, human approval workflows, tool invocation and inter-agent delegation (interface-only `Agent`/`Tool`/`AgentMemory`).
- [`12_Visualization_Design_Specification.md`](12_Visualization_Design_Specification.md) — `visualization` package: `Visualization`/`Renderer` (interface only), `Dashboard`/`Widget`/`Report`, rendering pipeline and export — the platform's final package; renders every lower package's already-structured output and performs no business computation of its own.

**Supporting documents:**

- `locked_ssot_documents/` — verbatim archival copies of the locked source documents these specifications are derived from.
- Architecture Decision Records (ADRs) — see [`docs/adr/`](../adr/) (`ADR-0006` through `ADR-0012` govern why each Intelligence-tier package exists as a separate layer) — and rendered layering/sequence diagrams under `docs/images/` are added as implementation proceeds.

Each design specification is implementation-ready: normative sections covering purpose, object model, sequence/class diagrams, error handling, testing strategy, certification requirements, and package acceptance criteria. Their companion implementation contracts live in [`docs/design/`](../design/README.md). The five Foundation specifications (`events`, `ontology`, `registry`/`plugins`, `connectors`, `kpis`) plus `analytics` and `decision` are implemented exactly as written — `decision`'s full module list (`DecisionModel`/`DecisionContext`, metadata, the full result-model family, pipeline composition, the plugin registry, rule composition/evaluation, `Policy` governance, `ThresholdDecisionStrategy`, scoring, ranking, explanation, prioritization, the interface-only `RootCauseAnalyzer`/`WhatIfEngine`, `ActionPlanner`, `AlertGenerator`, `RealTimeDecisionSession`/`BatchDecisionRunner`, and `DecisionAuditTrail` — see `src/mineproductivity/decision/README.md`) is complete per design spec §6, and `digital_twin`'s full module list (`Twin` — a `core.BaseEntity[str]` subclass — `TwinContext`, `TwinMetadata`/`TwinCategory`, the eleven category bases, `TwinStatus`, `TwinState`/`TwinSnapshot`, `TwinSynchronizer`/`SyncPolicy`, `TelemetryReading`, the interface-only `TwinSimulationModel`, `by_category`/`by_scope`, `TwinRepository` as a type alias over `core.BaseRepository[Twin, str]`, `TwinStateCache`, the `TwinResult` family, and the plugin registry — see `src/mineproductivity/digital_twin/README.md`) is likewise complete per its own design spec §6; `simulation`, `optimization`, `agents`, and `visualization` remain design-only — architecturally complete and locked, with no production implementation yet. `visualization` is the final package in the platform's architecture; no future package is anticipated above it.

## Dependencies

None (documentation only). The specifications describe packages that depend on `core` per the dependency direction in the root [README.md](../../README.md#architectural-layering--dependency-direction).

## Future Work

Add ADRs as significant architectural decisions are made during implementation. The five Foundation specifications (01–05) each record their own architecture decisions inline, in their own §35 Architecture Decisions section; specs 06–12 instead record theirs in a dedicated `docs/adr/ADR-000N-*.md` file each (`ADR-0006` through `ADR-0012`), a convention introduced starting with the Analytics milestone. `visualization` (spec 12) is the final package in the architecture; any future ADR would govern implementation-phase decisions, not a new package layer. Add rendered layering and sequence diagrams under `docs/images/` as an illustrated companion to the Mermaid diagrams already embedded in each specification. One post-v2.0 proposal — an analytics maturity assessment framework for mining enterprises — is recorded in the root [ROADMAP.md](../../ROADMAP.md)'s Future Architecture Proposals section; it is deliberately outside the locked architecture, and whether it would become a separate package (which would require an explicit architecture amendment to the "final package" statement above) or an application built on top of the platform is an explicitly deferred decision.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide, Parts I–III
- Learning & Benchmark Suite v1.0
