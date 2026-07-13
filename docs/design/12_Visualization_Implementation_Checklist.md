# Visualization — Implementation Checklist

**Package:** `mineproductivity.visualization`
**Governing specification:** [`docs/architecture/12_Visualization_Design_Specification.md`](../architecture/12_Visualization_Design_Specification.md)
**Architecture Decision Record:** [`docs/adr/ADR-0012-Visualization.md`](../adr/ADR-0012-Visualization.md)
**Status:** Implemented and released (software v1.11.0, 2026-07-12).

All items below are satisfied: the complete design spec §6 module list is implemented, the unit suite passes with ≥95% coverage (99% including branches), the five `examples/visualization/` scripts and both `benchmark/reports/visualization/` reports exist and are `mypy --strict`/`ruff`-clean, and the §35 acceptance proofs each run as dedicated tests. This is the final package milestone; the platform's architecture is complete. No architectural changes were made relative to the locked v1.4.0 design.

Binding, **locked** implementation contract for `visualization` — the seventh package built on top of the Foundation Layer and the **final** package in the platform's architecture, sitting directly above the now-locked `agents`. Nothing described here may be implemented before this checklist and its governing specification exist in reviewed form, and nothing may be implemented that is not represented by an item on this list. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [x] Design specification (`12_Visualization_Design_Specification.md`) read in full by the implementer, including every cross-reference to specs 01–11.
- [x] ADR-0012 read in full; the rationale for `visualization` existing as a separate package above `agents` (and for the interface-only treatment of `Visualization` and `Renderer`) is understood, not merely accepted.
- [x] `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, `kpis`, `analytics`, `decision`, `digital_twin`, `simulation`, `optimization`, `agents` available and importable, exactly as released; no lower package file is modified as a side effect of this work.
- [x] Confirmed: `visualization` imports nothing above itself — no future package exists (design spec §5, §34).
- [x] Confirmed: no lower package (`core` through `agents`) will be modified to import or otherwise reference `visualization` (design spec §5).
- [x] Confirmed: no concrete charting, templating, or document-generation library (e.g. Plotly, Matplotlib, Jinja2, WeasyPrint) is added as a dependency of this package — rendering backends are out of scope (design spec §4's non-responsibilities, §33's no-backend-coupling proof).

## Package Structure

- [x] `src/mineproductivity/visualization/` created matching design spec §6 exactly: `abstractions.py`, `presentation.py`, `theme.py`, `layout.py`, `widget.py`, `dashboard.py`, `dashboard_builder.py`, `report.py`, `report_builder.py`, `renderer.py`, `pipeline.py`, `export.py`, `discovery.py`, `persistence.py`, `_registry.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [x] `visualization/README.md` written following the `core/README.md` template.
- [x] Confirmed `renderer.py` (`Renderer`) and `abstractions.py` (`Visualization`) each contain zero concrete, non-test subclasses (mechanical grep/AST check — design spec §8, §16, §33's interface-purity proof).
- [x] Confirmed no module under `src/mineproductivity/visualization/` performs direct KPI, statistical, decision, twin-state, simulation-projection, solved-plan, or agent-decision computation of its own — every such value arrives via the corresponding lower package's public API (design spec §3.2, §33's no-fact-recomputation proof).
- [x] Confirmed no module under `src/mineproductivity/visualization/` imports, or contains a string reference to, `plotly`, `matplotlib`, `jinja2`, `weasyprint`, or any other charting/templating/document-generation library (design spec §33's no-backend-coupling proof).

## Public API

- [x] `visualization/__init__.py` exports exactly the symbol list in design spec §7, alphabetized `__all__`.
- [x] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py` and every existing package's own copy of it.
- [x] `TestNoForbiddenDependencies` AST-walks every `visualization` submodule confirming it imports nothing above itself — mirrors every existing package's own copy of this test (design spec §5).
- [x] A second, reverse-direction test asserts no file under `src/mineproductivity/{core,ontology,events,registry,plugins,connectors,kpis,analytics,decision,digital_twin,simulation,optimization,agents}/` imports `mineproductivity.visualization` (design spec §5) — the `agents`-package precedent for this test extended one final layer up.

## Visualization Abstractions (§8)

- [x] `Visualization` (§8) — `meta: ClassVar[VisualizationMetadata]`; one shared abstract method `_render(widget, *, context) -> PresentationModel`, mirroring `decision.DecisionModel`'s/`agents.Agent`'s shared-method posture.
- [x] `VisualizationContext` (§8) — `kpi_results`, `analytics_results`, `decision_results`, `twin_snapshot`, `simulation_results`, `optimization_results`, `agent_audit_entries`, each defaulting to an empty sequence or `None`; caller-assembles pattern only, no session-assembles variant.
- [x] Confirmed `Visualization` subclasses (of every category) are stateless — no instance attribute is mutated by any `_render` implementation; all statefulness lives in `Dashboard` (§10, §26, §29).

## Presentation Model (§9)

- [x] `PresentationModel` (§9) — frozen `core.BaseValueObject`; `category`, `title`, `series` (open mapping, default empty), `evidence_refs` (default empty tuple), `warnings` (default empty tuple).
- [x] Confirmed `PresentationModel` carries no rendered bytes/HTML/pixels of its own — that responsibility belongs exclusively to `Renderer` (§16).
- [x] Confirmed `PresentationModel.evidence_refs` is populated with real `KPIResult.code`/`AnalyticsResult.model_code`/`DecisionResult.model_code`/`OptimizationResult.run_id`/`AgentAuditEntry.agent_code`-shaped references in every concrete implementation's tests, never left empty when evidence was actually consulted.

## Dashboard Domain Model (§10)

- [x] `Widget` (§10) — frozen `core.BaseValueObject`; `code`, `visualization_code`, `binding` (open mapping, default empty).
- [x] `Layout` (§10) — frozen `core.BaseValueObject`; `code`, `slots` (open mapping, default empty); confirmed never parsed by this package's own code, only stored and handed to a `Renderer`.
- [x] `Dashboard` (§10) — subclasses `core.BaseEntity[str]` directly; `name`, `owner`, `widgets` (default empty tuple), `layout` (default `None`), `theme_code` (default `""`); modified exclusively via `dataclasses.replace`, never in place.
- [x] Confirmed `Dashboard` carries no `status` field and no `with_state()` method — a deliberate, documented departure from `Twin`/`SimulationRun`/`OptimizationRun`/`Task`'s own precedent (§10, §3.3).
- [x] Identity/equality proven: `Dashboard.__eq__`/`__hash__` inherited unchanged from `BaseEntity` (identity-based on `id`, ignoring `widgets`/`layout`/`theme_code`); no override anywhere in the package.

## Rendering Pipeline (§11)

- [x] `RenderingPipeline` (§6, §11) — resolves `widget.visualization_code` against `REGISTRY`, dispatches to `_render`, resolves `renderer_code` against `RENDERERS`, dispatches to `Renderer.render`.
- [x] `RenderingPipeline.render`'s dispatch sequence tested against design spec §11's sequence diagram exactly.
- [x] Confirmed a widget bound to incomplete or not-yet-computed evidence returns a `PresentationModel`/`RenderedOutput` carrying a warning, never a raised exception (§30's central rule).

## Dashboard Builder (§12)

- [x] `DashboardBuilder` (§12) — subclasses `core.BaseBuilder[Dashboard]` directly (the first concrete `core.BaseBuilder` subclass anywhere in this series); `with_name`, `with_widget`, `with_layout`, `with_theme` fluent methods; `build()` raises `VisualizationValidationError` for an empty `name`/`owner`.
- [x] Confirmed `DashboardBuilder.build_result()` is the inherited, unoverridden `core.BaseBuilder.build_result()` — no second non-raising variant introduced.
- [x] Confirmed `DashboardBuilder.reset()` is exercised in at least one test proving the builder is reusable after a `build()` call, per `core.BaseBuilder.reset()`'s own contract.

## Report Model (§13)

- [x] `Report` (§13) — frozen `core.BaseValueObject`; `report_code`, `generated_at`, `sections` (default empty tuple of `RenderedOutput`), `warnings` (default empty tuple).
- [x] Confirmed no `ReportRepository` exists anywhere in the package — `Report` is a produced-once artifact, never independently persisted, the same treatment every prior `*Result` type already receives.

## Report Builder (§14)

- [x] `ReportBuilder` (§14) — subclasses `core.BaseBuilder[Report]` directly; `with_section(widget, *, context, renderer_code)` composes `RenderingPipeline.render` for each section; `build()` assembles the final `Report`.
- [x] Confirmed `ReportBuilder` never duplicates `RenderingPipeline`'s own dispatch logic — every section is produced by an actual `RenderingPipeline.render` call, never a re-implementation of it.
- [x] Confirmed a section that produced a warning-carrying `RenderedOutput` preserves that warning on the final `Report.warnings`, never silently drops it.

## Worked Examples (§15, §19)

- [x] A scripted integration test reproduces design spec §15's worked example shape (a multi-widget dashboard combining a `KPI_CARD`, an `OPTIMIZATION_COMPARISON`, and an `AGENT_EXPLANATION` widget), each rendered independently via `RenderingPipeline`.
- [x] A scripted integration test reproduces design spec §19's worked example shape (the same widgets composed into an exported `Report` via `ReportBuilder`), proving the live-render and export code paths never diverge (§18, §33's export round-trip test).

## Renderer (§16)

- [x] `RendererMetadata` (§16) — `code`, `description`, `version` (default `"1.0.0"`).
- [x] `Renderer` (§16) — `meta: ClassVar[RendererMetadata]`; `render(model, *, context) -> RenderedOutput` abstract; zero concrete subclasses shipped.
- [x] `RenderedOutput` (§16) — frozen `core.BaseValueObject`; `format`, `payload`, `warnings` (default empty tuple).
- [x] Confirmed this package never invokes or interprets `Widget.binding`/`Layout.slots` on a `Renderer`'s behalf — a concrete `Renderer` implementation interprets both entirely on its own.

## Domain-Specific Presentation Views (§17)

- [x] Confirmed `SIMULATION_PLAYBACK`, `DIGITAL_TWIN_VIEW`, `OPTIMIZATION_COMPARISON`, and `AGENT_EXPLANATION` are each an ordinary `VisualizationCategory` member (§26) — no separate ABC, no separate object model, no per-category module exists for any of the four.
- [x] Unit tests confirm at least one flagship `Visualization` implementation per domain-specific category binds to exactly the `VisualizationContext` field its own category name implies (e.g. `SIMULATION_PLAYBACK` reads `simulation_results`, never `optimization_results`).

## Export (§18)

- [x] `ExportRequest` (§18) — frozen `core.BaseValueObject`; `renderer_code`, `dashboard_id` (default `None`), `report` (default `None`).
- [x] `ExportResult` (§18) — frozen `core.BaseValueObject`; `format`, `payload`, `exported_at`.
- [x] Confirmed `Export` introduces no separate execution mechanism — every export is an ordinary `RenderingPipeline.render` call targeting a file-producing `Renderer`, wrapped in an `ExportResult`.
- [x] Confirmed `Export` shares no code with `connectors` — the two are documented as opposite-direction concerns (§5, §18).

## Visualization Registry and Renderer Registry (§20)

- [x] `visualization._registry.REGISTRY`/`register` (§20) — `Registry[str, type[Visualization]]`, raising `VisualizationValidationError` for an empty code and `VisualizationVersionConflictError` for a materially-different re-registration under an existing code.
- [x] `visualization._registry.RENDERERS`/`register_renderer` (§20) — `Registry[str, type[Renderer]]`, identical error semantics, specialized for `Renderer`.
- [x] `EntryPointSpec(group="mineproductivity.visualization", target_registry="visualization")` and `EntryPointSpec(group="mineproductivity.visualization.renderers", target_registry="visualization.renderers")` discovery wired via `registry.EntryPointDiscovery` (§28).
- [x] Confirmed `REGISTRY` and `RENDERERS` are never merged into one — a `Visualization` type and a `Renderer` type remain orthogonal registrable concepts throughout the codebase.

## Theme (§21)

- [x] `Theme` (§21) — frozen `core.BaseValueObject`; `code`, `palette` (open mapping, default empty), `typography` (open mapping, default empty).
- [x] Confirmed no `Registry` exists for `Theme` — it is plain configuration data, never looked up polymorphically.

## Persistence (§22)

- [x] `DashboardRepository` implemented as `type DashboardRepository = BaseRepository[Dashboard, str]` — a type alias, **not** a new ABC or subclass.
- [x] Reference implementation uses `core.InMemoryRepository[Dashboard, str]()` directly, with zero new persistence code.
- [x] Test suite for `DashboardRepository` behavior written against the `core.BaseRepository[Dashboard, str]` contract alone, never against `InMemoryRepository`-specific internals (§33's repository-substitutability proof).

## Versioning (§23)

- [x] `VisualizationMetadata.version`/`RendererMetadata.version` (a registered type's own SemVer) confirmed independent of any `Dashboard`'s own contents — no code path derives one from another.
- [x] `VisualizationVersionConflictError` raised at registration time for a materially-different re-registration under an existing `VisualizationMetadata`/`RendererMetadata` code — never deferred.
- [x] Confirmed two `Dashboard`s sharing the same `name` under different `owner`s is never treated as a conflict anywhere in the codebase.

## Caching (§24)

- [x] Confirmed no dedicated cache module exists anywhere in the package (§24's documented, deliberate non-need; §32's recorded anti-pattern against introducing one "for consistency").
- [x] Confirmed any `Renderer`-internal memoization is documented as that `Renderer`'s own implementation detail, never a shared package-level cache abstraction.

## Validation (§25)

- [x] `VisualizationMetadata.validate()`/`RendererMetadata.validate()` — non-empty `code`, category matches the closed `VisualizationCategory` namespace where applicable.
- [x] `Dashboard.validate()` — non-empty `name` and `owner`.
- [x] `Widget.validate()` — non-empty `code` and `visualization_code`.
- [x] `Layout.validate()` — non-empty `slots`.
- [x] `Theme.validate()` — non-empty `code`.

## Metadata (§26)

- [x] `VisualizationCategory` enum (§26) — exactly `Chart`/`Graph`/`KpiCard`/`Timeline`/`SimulationPlayback`/`DigitalTwinView`/`OptimizationComparison`/`AgentExplanation`; a closed enum, adding a member is a governance-reviewed change.
- [x] `VisualizationMetadata` (§26) — `code`, `category`, `description`, `version` (default `"1.0.0"`); `validate()` rejects an empty `code`.
- [x] Confirmed `VisualizationMetadata.code` names a visualization **type** and is never confused with a `Widget.code` anywhere in the codebase.

## Discovery (§27)

- [x] `by_theme()`/`by_owner()` (§27) — plain `core.PredicateSpecification` factories; composed with `DashboardRepository.list()`; confirmed to return an empty sequence (never raise) for a filter matching nothing.
- [x] Confirmed the three-way distinction (`REGISTRY`/`RENDERERS` = which types are known; `DashboardRepository` = which dashboard instances currently exist; `discovery.py` = query facade over the instance store) is never conflated anywhere in the codebase.

## Extension Points & Plugin Integration (§28)

- [x] Entry-point groups `mineproductivity.visualization` and `mineproductivity.visualization.renderers` documented and wired exactly per §28.
- [x] A scripted integration test exercises a fixture "sitepack" plugin (registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern) that subclasses `Visualization`, proving the platform-side dispatch and registration path works end to end.
- [x] A second fixture plugin subclasses `Renderer` and is proven discoverable via `RENDERERS` independently of the `Visualization` fixture.

## Thread Safety & Concurrency (§29)

- [x] `Visualization` instances (of every category) confirmed stateless and safe to share/read across threads with no locking.
- [x] `Dashboard` instances confirmed immutable and safe to share/read across threads with no locking.
- [x] `DashboardRepository`'s per-id write serialization contract documented and tested against any production-grade implementation candidate; confirmed the bare `core.InMemoryRepository` reference implementation provides **no** locking of its own — any concurrent-write test against it must add external synchronization itself.
- [x] `visualization.REGISTRY`/`visualization.RENDERERS` each confirmed read-only and thread-safe after startup discovery, inheriting `Registry`'s own contract.
- [x] Independent widget renders (different widgets, or the same widget under different contexts) proven to execute fully in parallel without contention.

## Error Handling (§30)

- [x] Full exception hierarchy (design spec §6 `exceptions.py`): `VisualizationValidationError`, `DashboardNotFoundError`, `RenderingError`, `VisualizationVersionConflictError` — each subclassing the matching `core` or `registry` exception (`VisualizationVersionConflictError` subclasses `registry.RegistrationError`; the rest subclass a `core` exception).
- [x] Confirmed no `Visualization._render`/`Renderer.render` implementation raises for a legitimately incomplete widget binding or empty evidence — returns a `PresentationModel`/`RenderedOutput` carrying a warning instead.

## Security (§31)

- [x] Confirmed no concrete `Renderer` implementation evaluates `Widget.binding`/`Layout.slots` as executable code or a dynamic template — both are treated strictly as data.
- [x] Confirmed `by_owner` (§27) is documented and tested as a convenience query only, never as an access-control boundary.
- [x] Confirmed no new cryptographic, network, or credential-handling surface is introduced by this package.

## Tests

- [x] `tests/unit/visualization/` mirrors `src/mineproductivity/visualization/` 1:1.
- [x] Coverage ≥95%.
- [x] Unit tests per concrete visualization category — at least one flagship visualization per `VisualizationCategory`, each against a scripted widget and context with a known expected `PresentationModel` (§33).
- [x] Identity/equality tests, builder contract tests, rendering-dispatch tests, interface-only ABC contract tests, registry/discovery isolation tests, export round-trip tests, warning-propagation tests, and concurrency stress tests as enumerated in design spec §33.
- [x] The five package acceptance proofs in design spec §33 (no-fact-recomputation, immutability, interface-purity, no-architectural-drift, no-backend-coupling) each independently verified and recorded in the PR description.

## Documentation

- [x] `visualization/README.md` complete.
- [x] Every registered `Visualization`/`Renderer` type's docstring restates its `VisualizationMetadata.description`/`RendererMetadata.description` for source-level readability.

## Examples

- [x] `examples/visualization/01_single_widget_render.py` — a single `Visualization` category rendering one `Widget` end-to-end via `RenderingPipeline`.
- [x] `examples/visualization/02_multi_source_dashboard.py` — the design spec §15 worked example (`KPI_CARD`/`OPTIMIZATION_COMPARISON`/`AGENT_EXPLANATION` widgets composed via `DashboardBuilder`), end-to-end.
- [x] `examples/visualization/03_export_report.py` — the design spec §19 worked example (`ReportBuilder` composing the same widgets into an exported `Report`).
- [x] `examples/visualization/04_simulation_playback.py` — a `SIMULATION_PLAYBACK`-category widget rendering a `SimulationResult`'s state trajectory.
- [x] `examples/visualization/05_plugin_visualization_and_renderer.py` — a third-party-style `Visualization` and `Renderer` subclass registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern.
- [x] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [x] `DashboardRepository.get()`/`list()` latency at representative dashboard-population scale, recorded in `benchmark/reports/visualization/`.
- [x] A multi-widget dashboard's parallel-render throughput at representative widget counts, recorded.

## Certification

- [x] Design spec §33's five package acceptance proofs pass and are recorded in the PR description (duplicated here from Tests for merge-gate visibility).

## Type Hints, Mypy, Ruff, Coverage

- [x] 100% type-hinted; `mypy --strict` clean.
- [x] `ruff check` and `ruff format --check` clean.
- [x] Coverage report attached; ≥95%.

## Release

- [x] `CHANGELOG.md` updated.
- [x] Root README dependency diagram cross-checked — confirm `visualization` gained no forbidden import, and confirm no lower package gained a new `visualization` import.
- [x] Version bump proposed and reviewed.
- [x] Design spec §33's acceptance proofs re-verified as final merge gate.

---

*Derived from [`12_Visualization_Design_Specification.md`](../architecture/12_Visualization_Design_Specification.md). Keep in sync with the governing specification and with [`ADR-0012-Visualization.md`](../adr/ADR-0012-Visualization.md).*
