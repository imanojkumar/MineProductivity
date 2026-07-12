# mineproductivity.visualization

## Purpose

The presentation layer (design spec 12) — the final package in the platform's architecture, built directly above `agents`. It defines *what* is shown (`Visualization`/`PresentationModel`), *where* it lives (`Widget`/`Dashboard`/`Layout`/`Theme`), and *how* rendering is orchestrated (`RenderingPipeline`, `Report`/`ReportBuilder`, `ExportRequest`/`ExportResult`) — while `Visualization` and `Renderer` remain interface-only extension points: choosing a charting, templating, or document-generation backend is exactly the implementation decision this package excludes.

## Governing documents

- [`docs/architecture/12_Visualization_Design_Specification.md`](../../../docs/architecture/12_Visualization_Design_Specification.md)
- [`docs/design/12_Visualization_Implementation_Checklist.md`](../../../docs/design/12_Visualization_Implementation_Checklist.md)
- [`docs/adr/ADR-0012-Visualization.md`](../../../docs/adr/ADR-0012-Visualization.md)

## Scope

**What belongs here:** presentation contracts (eight closed `VisualizationCategory` members — four general-purpose shapes, four domain-specific views), the dashboard/report domain model, the one rendering pipeline shared by live and exported output, and the two type registries.

**What must never belong here:** a concrete `Visualization` or `Renderer` implementation; any charting/templating/document-generation library coupling; any recomputation of a KPI, statistical, decision, twin-state, simulation, optimization, or agent fact a lower package already owns.

## Dependencies

**Depends on:** `core`, `registry`, `kpis`, `analytics`, `decision`, `digital_twin`, `simulation`, `optimization`, `agents` (`AgentAuditEntry` as renderable evidence).

**Depended on by:** nothing — `visualization` is the platform's final package; it imports nothing above itself.

## Extension points

Register a concrete `Visualization` with `@register` (entry-point group `mineproductivity.visualization`) and a concrete `Renderer` with `@register_renderer` (group `mineproductivity.visualization.renderers`); implement a `DashboardRepository` backend as a `core.BaseRepository[Dashboard, str]`. `Theme` is plain configuration data — deliberately not registrable.
