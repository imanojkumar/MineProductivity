# Architecture Documentation

## Purpose

Companion documentation for the Master Architecture Handbook v1.0 — the locked SSOT describing MineProductivity's overall system architecture, layering, and design principles.

## Scope

Architectural rationale, layering diagrams, dependency rules, and cross-cutting design decisions (Clean Architecture, DDD, event-sourcing, ontology-first modeling). Does not include package-level implementation detail — that belongs in each package's own `README.md` under `src/mineproductivity/`.

## Responsibilities

- Explain the inward-pointing dependency direction between `core`, `ontology`, `events`, `kpis`, `analytics`, `decision`, and `digital_twin`.
- Document forbidden import patterns and architectural boundaries.
- Serve as the entry point for new contributors to understand system shape before reading code.

## Contents

- `01_Event_Framework_Design_Specification.md` — `events` package: `BaseEvent`, `EventEnvelope`, `EventStore`, `EventBus`, replay/time-travel, idempotency.
- `02_Ontology_Framework_Design_Specification.md` — `ontology` package: the ten sub-ontology families (equipment, material, location, organization, production, maintenance, cost, quality, safety, environmental) and the Knowledge Graph projection contract.
- `03_Registry_Framework_Design_Specification.md` — `registry` + `plugins` packages: the generic registration/discovery mechanism every domain registry (KPI, Connector, Ontology, Analytics) specializes.
- `04_Connector_Framework_Design_Specification.md` — `connectors` package: the `FMSConnector` contract, reference connectors (CSV/Excel/REST/GraphQL/Kafka/MQTT), and OEM adapter shapes (MineStar, DISPATCH, Wenco, Modular Mining, Hexagon).
- `05_KPI_Engine_Design_Specification.md` — `kpis` package: `BaseKPI`, the 29-field `KPIMetadata` schema, the dependency graph, aggregation semantics, and vectorized execution backends. The platform's most important design specification.
- `locked_ssot_documents/` — verbatim archival copies of the locked source documents these specifications are derived from.
- Architecture Decision Records (ADRs) — see `docs/adr/` — and rendered layering/sequence diagrams under `docs/images/` are added as implementation proceeds.

Each design specification is implementation-ready: 37 normative sections covering purpose, object model, sequence/class diagrams, error handling, testing strategy, certification requirements, and package acceptance criteria. Their companion implementation contracts live in [`docs/design/`](../design/README.md). All five specifications above (`events`, `ontology`, `registry`/`plugins`, `connectors`, `kpis`) are now implemented against exactly as written; `analytics`, `decision`, and `digital_twin` remain design-only.

## Dependencies

None (documentation only). The specifications describe packages that depend on `core` per the dependency direction in the root [README.md](../../README.md#architectural-layering--dependency-direction).

## Future Work

Add ADRs as significant architectural decisions are made during implementation (see each design specification's own §35 Architecture Decisions for decisions already recorded at design time). Add rendered layering and sequence diagrams under `docs/images/` as an illustrated companion to the Mermaid diagrams already embedded in each specification.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide, Parts I–III
- Learning & Benchmark Suite v1.0
