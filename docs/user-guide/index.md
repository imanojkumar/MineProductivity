# User Guide

MineProductivity is built from a small set of first principles. Understanding them makes every package predictable.

## Engineering philosophy

| Principle | What it means here |
|---|---|
| **Clean Architecture** | Dependencies point inward; `core`/`ontology` know nothing about `connectors`, `agents`, or `visualization`. |
| **Domain-Driven Design** | Package names are domain concepts (`kpis`, `digital_twin`, `decision`), not technical layers (`services`, `helpers`). |
| **SOLID** | Each package has one reason to change; extension happens via `plugins`/`registry`, not by editing `core`. |
| **Plugin-first** | New KPIs, connectors, analytics, agents, and renderers are registered, not hard-coded. |
| **Event-first** | Events are the immutable source of truth; everything else is a derived, rebuildable projection. |
| **Metadata-first** | No KPI or dataset ships without units, provenance, and versioning metadata. |
| **Ontology-first** | Domain concepts are defined in `ontology` before any package models them in code. |

## The shape of the platform

Work flows up the locked dependency chain. Each layer consumes the layer below and never the reverse:

- **Foundation** - `core` → `ontology` → `events` → `kpis`: primitives, the typed domain vocabulary, the event-sourced system of record, and the metadata-first KPI Engine.
- **Intelligence** - `analytics` → `decision` → `digital_twin` → `simulation` → `optimization` → `agents` → `visualization`: statistical characterization, prescriptive recommendations, stateful representation, projection, prescriptive search, autonomous orchestration, and presentation.
- **Cross-cutting** - `registry`, `plugins`, `connectors`: importable by any layer, dependent on none of the domain layers.

## Extension points

The platform ships **zero** concrete implementations of its interface-only extension points - each is a deliberate plugin seam, enforced by tests:

- Solver adapters (`optimization`), reasoning backends and tools (`agents`), rendering backends (`visualization`)
- Forecasting/anomaly models (`analytics`), root-cause/what-if engines (`decision`), twin-simulation and methodology models (`digital_twin`/`simulation`)
- Connectors (`connectors`), KPIs (`kpis`), and governed artifacts (scenarios, problems, policies, themes) authored as data

To learn a specific package's contract, read its [package page](../packages/index.md); to see it working, follow its [tutorial](../tutorials/index.md); to understand *why* it exists as a separate layer, read the [architecture](../architecture/README.md) and its [ADR](../adr/index.md).
