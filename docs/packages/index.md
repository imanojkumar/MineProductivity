# Packages

Each package documents its own purpose, dependency rules, public API, extension guide, design rationale, and anti-patterns. These pages reuse the packages' own `README.md` files verbatim - the same documentation enforced by each package's `test_public_api.py`.

For the symbol-level, docstring-generated reference, see the [API Reference](../api-reference/index.md).

## Foundation

| Package | Responsibility |
|---|---|
| [core](core.md) | Framework primitives: entities, value objects, identifiers, specifications, repositories, builders. |
| [ontology](ontology.md) | The typed, machine-readable domain vocabulary (ten sub-ontology families) and the Knowledge Graph projection. |
| [events](events.md) | The immutable, append-only event model (Event Sourcing): store, bus, replay/time-travel, codecs. |
| [registry](registry.md) | The generic, type-safe registration/discovery mechanism every domain registry specializes. |
| [plugins](plugins.md) | The plugin lifecycle layer built on `registry`: manifests, states, activation ordering. |
| [connectors](connectors.md) | The vendor-neutral ingestion boundary: the `FMSConnector` contract and reference connectors. |
| [kpis](kpis.md) | The metadata-first, self-describing KPI Engine and the Standard Library. |

## Intelligence

| Package | Responsibility |
|---|---|
| [analytics](analytics.md) | Statistical and analytical computation built on `kpis`. |
| [decision](decision.md) | The prescriptive layer: rules, policies, ranking, explanation, alerting, audit. |
| [digital_twin](digital_twin.md) | The stateful representation layer: `Twin`, synchronization, snapshots, telemetry. |
| [simulation](simulation.md) | The projection layer: scenarios, runs, experiments, methodology extension points. |
| [optimization](optimization.md) | The prescriptive-search layer: six solving paradigms, plan comparison, sensitivity. |
| [agents](agents.md) | The model-independent orchestration layer: tasks, policies, approval, delegation, audit. |
| [visualization](visualization.md) | The presentation layer: dashboards, reports, the rendering pipeline - the final package. |
