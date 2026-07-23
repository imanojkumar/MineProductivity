# Package Tutorial 13 — Visualization (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 13 of 13 · **the final package**"
    Deep, full-surface tutorial for `mineproductivity.visualization` — presenting
    already-governed evidence to a human, without the platform ever depending on a
    charting library. Authored to **Package Tutorial Template v1.0** under the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).
    This tutorial closes the Learning Suite.

## Objective

Master the working surface of `mineproductivity.visualization`: the interface-only
`Visualization`/`Renderer`, the `PresentationModel` (structure, not bytes), the one
`RenderingPipeline`, `Widget`/`Dashboard`/`Layout`/`Theme`,
`DashboardBuilder`/`ReportBuilder`, export, the dual `REGISTRY`/`RENDERERS`, and —
the payoff — **a plugin visualization and renderer**.

All 29 public symbols (`mineproductivity.visualization.__all__`) are accounted for
under the **coverage convention** (§5): **21 [deep]** / **8 [ref]**. Public APIs
only.

## Prerequisites

- Package Tutorials [1 — Core](01_core.md), [6 — KPIs](06_kpis.md): a widget
  presents a `KPIResult`; a `PresentationModel` is a `core.BaseValueObject` (§3).
- [Fundamentals L10 — Visualization](../fundamentals/10_visualization.md): the intro —
  present a governed fact; structure, not pixels; qualify, don't coerce.

This tutorial **builds on** L10.

## Running the examples

Every code block below is executed and its output pasted verbatim. Five scripts:

```bash
pip install -e ".[analytics]"
python examples/visualization/01_single_widget_render.py   # ...and 02–05
```

---

## 1. Why this package exists

Every layer below governed a number; the last step is to **show a human** — a KPI
card, a handover dashboard, an exported report. `visualization` does that with one
firm rule: it **does no business computation and cannot**. It takes evidence the
lower layers already governed (`KPIResult`s, plan comparisons, agent notes) and
arranges it — so a dashboard can never disagree with the KPI engine, because a
dashboard cannot do arithmetic.

Two design choices carry the whole package. A `PresentationModel` carries
**structure, not bytes** — "a KPI card titled PROD.TPH, value 1212, unit t/h" — so
the *same* model renders unchanged to a terminal, an SVG dashboard, or a PDF. And
the package **ships zero renderers**: the charting/templating library lives in a
plugin, never in the locked package (a test enforces it — ADR-0012).

## 2. Architectural role

`visualization` is the top of the stack — it consumes everything and produces
nothing anyone re-derives from:

```
core ─► … ─► optimization ─► agents ─► visualization
```

It presents governed evidence from *every* layer: a KPI card (kpis), a plan
comparison (optimization), a handover note (agents), a simulation playback. It is
the one layer that knows about presentation and nothing about tonnes.

## 3. Integration with adjacent layers

**Every layer — the evidence:** a `VisualizationContext` carries already-governed
results (`kpis.KPIResult`s, and — assembled by the caller — optimization/agents/
simulation outputs); a `Widget` binds a visualization to the evidence it wants. The
dashboard example assembles three *different-source* widgets (§8.2). Visualization
consumes; it re-derives nothing.

**`registry` (Tutorial 4) — dual registries:** `REGISTRY` (visualizations) and
`RENDERERS` (renderers) are `registry.Registry`s; `@register`/`@register_renderer`
add them, discovered by entry point (§13).

**`core` (Tutorial 1):** `PresentationModel`, `Widget`, `Dashboard`, `Report` are
`core.BaseValueObject`s — a model carries no colours, dimensions, or bytes.

**No upward layer** — this is the last package. It closes the chain the whole
Learning Suite has been building: *events record, kpis measure, analytics
characterise, decision recommends, twin projects, simulation/optimization plan,
agents orchestrate, visualization shows a human* — each layer consuming the one
below and re-deriving nothing.

## 4. Package structure

| Group | Module(s) | Public symbols |
|---|---|---|
| The contracts | `abstractions`, `renderer` | `Visualization`, `Renderer`, `RenderedOutput`, `RendererMetadata` |
| The model & pipeline | `presentation`, `pipeline` | `PresentationModel`, `RenderingPipeline` |
| Widgets & dashboards | `widget`, `dashboard`, `dashboard_builder`, `layout`, `theme` | `Widget`, `Dashboard`, `DashboardBuilder`, `Layout`, `Theme` |
| Reports & export | `report`, `report_builder`, `export` | `Report`, `ReportBuilder`, `ExportRequest`, `ExportResult` |
| Metadata & context | `metadata`, `abstractions` | `VisualizationMetadata`, `VisualizationCategory`, `VisualizationContext` |
| Registry, discovery, persistence | `_registry`, `discovery`, `persistence` | `REGISTRY`, `RENDERERS`, `register`, `register_renderer`, `by_owner`, `by_theme`, `DashboardRepository` |
| Exceptions | `exceptions` | `RenderingError`, `DashboardNotFoundError`, `VisualizationValidationError`, `VisualizationVersionConflictError` |

## 5. Public APIs

All 29 exports under the **coverage convention**:

**The spine — [deep]**
: `Visualization`, `Renderer`, `RenderedOutput`, `PresentationModel`,
  `RenderingPipeline`, `Widget`, `Dashboard`, `DashboardBuilder`, `Report`,
  `ReportBuilder`, `ExportRequest`, `ExportResult`, `VisualizationContext`,
  `VisualizationMetadata`, `VisualizationCategory`, `REGISTRY`, `RENDERERS`,
  `register`, `register_renderer`, `by_owner`, `by_theme`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What / when |
|---|---|---|
| Presentation detail | `Layout`, `Theme`, `RendererMetadata` | A dashboard's layout and theme (structure/intent, not CSS); a renderer's declared metadata. |
| Persistence | `DashboardRepository` | Stores dashboards for retrieval by owner/theme. |
| Exceptions | `RenderingError`, `DashboardNotFoundError`, `VisualizationValidationError`, `VisualizationVersionConflictError` | A render failure, unknown dashboard, invalid metadata, duplicate code. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. No business computation — ever.** A `Visualization` cannot compute a KPI; it
consumes `context.kpi_results` and arranges them. That "limitation" is why the layer
is safe.

**B. The model carries structure, not bytes.** A `PresentationModel` says *what* to
show (title, series, evidence refs), never *how many pixels*. So one model renders
unchanged to text, SVG, or PDF.

**C. One pipeline, two interface-only contracts.** `RenderingPipeline` is the single
path: `Visualization` → `PresentationModel` → `Renderer` → `RenderedOutput`. Both
`Visualization` and `Renderer` ship **zero** implementations.

**D. Qualify, don't coerce.** Missing evidence yields a model carrying a *warning*
(the renderer prints `UNAVAILABLE`), never a fabricated `0.0` and never an exception
that blanks the whole dashboard.

**E. Compose, don't couple.** `DashboardBuilder`/`ReportBuilder` assemble widgets
from *any* source; export is the *same* render path wrapped in an `ExportResult`.

## 7. Real mining examples

The walkthroughs present a shift handover: a single `PROD.TPH` card (present and
missing), a three-source dashboard (KPI + plan comparison + agent note), an exported
report, and a simulation playback — plus a site-pack SVG gauge plugin (§13).

## 8. Step-by-step walkthroughs

### 8.1 Render one widget — present, and missing

The pipeline renders a `Widget` bound to `PROD.TPH`. With evidence present, it emits
a `RenderedOutput`; with evidence missing, it **qualifies** — a warning, never a
zero. Running
[`01_single_widget_render.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/01_single_widget_render.py):

```text
--- 1. Render with the evidence present ---
format='text' payload='PROD.TPH: 1212.1 t/h' warnings=()

--- 2. Render with the evidence missing: qualify, don't coerce (sec. 30) ---
payload='PROD.TPH' warnings=("no KPIResult for 'PROD.TPH' in context",)
```

A control room that silently shows `0.0 t/h` when the feed dies is dangerous — an
operator reads "fleet stopped". The platform shows the title and a warning, and tells
you why.

### 8.2 A multi-source dashboard

`DashboardBuilder` composes three widgets from **three different lower layers** — a
KPI card, an optimization plan comparison, an agent handover note — and each renders
independently through the *one* pipeline. Running
[`02_multi_source_dashboard.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/02_multi_source_dashboard.py):

```text
--- 1. Build a dashboard from three different-source widgets ---
dashboard id=DASH-a029828a9030 owner='shift-supervisor-a' widgets=3

--- 3. Render each widget independently through the one pipeline ---
  tph_card: PROD.TPH :: {'value': 1212.1}
  plan_compare: Plan comparison :: {'objective_values': (51500.0,)}
  agent_note: Handover note :: {'premises': ('Reassign two trucks to the north pit',)}
```

Three layers of the platform, one presentation model each, one pipeline — and the
dashboard did no arithmetic on any of them.

### 8.3 Report, export, and playback

The *same* widgets compose into a `Report` via `ReportBuilder`, and **export is the
same code path** wrapped in an `ExportResult` — the exported payload matches the live
render exactly. A simulation playback renders pre-computed frames through the same
pipeline. Running
[`03_export_report.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/03_export_report.py)
and
[`04_simulation_playback.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/04_simulation_playback.py):

```text
--- 2. Compose the same widgets into a Report via ReportBuilder ---
report 'SHIFT.Handover': 2 sections
  section payload: 'PROD.TPH=1212.1'
  section payload: 'UTIL.OEE=0.78'

--- 3. Export is the same code path, wrapped in an ExportResult (sec. 33) ---
export payload matches live render: True ('PROD.TPH=1212.1')

--- (playback) Render the playback view through the pipeline ---
Night-shift throughput playback: 06:00 4200t/h | 07:00 4320t/h | ... | 11:00 4800t/h
```

That export matches the live render is the payoff of "one pipeline": a report is not
a second rendering path that can drift — it is the same models rendered again.

## 9. Repository example reuse

The five `visualization` scripts were each executed (exit `0`), output above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_single_widget_render.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/01_single_widget_render.py) | `Widget`, `PresentationModel`, `RenderingPipeline`, `RenderedOutput`, `VisualizationContext` | §8.1 |
| [`02_multi_source_dashboard.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/02_multi_source_dashboard.py) | `Dashboard`, `DashboardBuilder`, `Widget`, `by_owner` | §8.2 |
| [`03_export_report.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/03_export_report.py) | `Report`, `ReportBuilder`, `ExportRequest`, `ExportResult` | §8.3 |
| [`04_simulation_playback.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/04_simulation_playback.py) | `VisualizationContext`, `RenderingPipeline`, `VisualizationCategory` | §8.3 |
| [`05_plugin_visualization_and_renderer.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/05_plugin_visualization_and_renderer.py) | `Visualization`, `Renderer`, `VisualizationMetadata`, `RendererMetadata`, `register`, `register_renderer`, `REGISTRY`, `RENDERERS` | §13 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Computing a KPI in a widget | The dashboard disagrees with the KPI engine | Consume `context.kpi_results` |
| Defaulting missing data to `0.0` | The control room reads "stopped" — dangerous | Warning + `UNAVAILABLE` |
| Putting bytes/colours in `PresentationModel` | Couples the model to one backend; the PDF path breaks | Keep it structural |
| Importing a charting library in the package | Violates ADR-0012; a test fails | Import it in your plugin renderer |
| Raising on missing evidence | One dead feed blanks the whole dashboard | Qualify, don't coerce |
| A separate export rendering path | It drifts from the live view | Export re-renders the same models |

## 11. Best practices

- **Never compute in a visualization** — if you are dividing, you are in the wrong layer.
- **Return a warning-carrying model for missing evidence** — never `0.0`, never an exception.
- **Keep `PresentationModel` backend-free** — no colours, dimensions, or bytes.
- **Import charting libraries only in a plugin renderer.**
- **Set evidence refs** so a viewer can trace a card to its governed source.
- **Compose dashboards/reports from any source**; export via the same pipeline.

## 12. Performance considerations

- **Rendering is structural** — building a `PresentationModel` is cheap; the heavy
  work (rasterising an SVG, laying out a PDF) lives in the plugin renderer.
- **One pipeline** means one thing to cache/optimise; a report reuses live models.
- **`DashboardRepository` + `by_owner`/`by_theme`** retrieve dashboards without rebuilds.
- **Models are frozen value objects** — safe to share across renderers and threads.

## 13. Extension points — a plugin visualization and renderer

`visualization` ships **zero** concrete visualizations or renderers (ADR-0012). The
extension point is to implement `Visualization` (produce a `PresentationModel`) and
`Renderer` (turn it into a `RenderedOutput`), declare
`VisualizationMetadata`/`RendererMetadata`, and register with
`@register`/`@register_renderer` — the charting/templating library lives in your
plugin. The reused
[`05_plugin_visualization_and_renderer.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/visualization/05_plugin_visualization_and_renderer.py)
discovers a site-pack SVG gauge and renderer through the real entry-point path:

```text
--- 1. visualization ships zero concrete views or renderers ---
site-pack views before:     []
site-pack renderers before: []

--- 2. A site pack declares both via pyproject.toml entry-points ---
views     discover() is_ok: True loaded: ('sitepack',)
renderers discover() is_ok: True loaded: ('sitepack',)
registered view: KPI_CARD.SitePackGauge; registered renderer: SVG.SitePack

--- 3. The discovered plugin renders like any built-in would ---
format='svg' payload='<svg><text>PROD.TPH: 1212.1</text></svg>'
```

The **dual registries** mirror agents' `REGISTRY`/`TOOLS`: a visualization (what to
show) and a renderer (how to emit it) are independently versioned, discoverable
capabilities — the *same* `PresentationModel` can be emitted by an SVG renderer, a
terminal renderer, or a PDF renderer, each a separate plugin.

!!! note "The locked package imports no charting library"
    A test enforces that no charting/templating string appears in the package at all
    (ADR-0012). matplotlib, Jinja, a PDF library — all live in a plugin. That is what
    lets one `PresentationModel` render to a terminal, an SVG dashboard, or a PDF
    unchanged, and lets the locked platform stay dependency-light.

## 14. Exercises

1. **Add a renderer.** Write an `SvgRenderer` producing `<svg>...</svg>` from the *same*
   `PresentationModel` a text renderer consumes. You did not touch the visualization — why
   is that the point?
2. **Kill the feed.** Render with an empty `VisualizationContext`. What does an operator
   see? Compare it to a dashboard showing `0.0`. Which would you rather have at 3 a.m.?
3. **Compose a dashboard.** Use `DashboardBuilder` to combine a KPI card, an optimization
   plan card, and an agent note; render each through the one pipeline.
4. **Export = live.** Build a `Report`, export it, and assert the exported payload equals
   the live render. Why is that guaranteed?
5. **Reflect on the chain.** `analytics` ships no forecaster, `decision` no root-cause
   engine, `simulation`/`optimization`/`agents`/`visualization` no concrete backend. Write
   down the single principle behind all of those refusals.

## 15. Reference solutions

??? success "Solution 1 — Add a renderer"
    Implement `Renderer` to turn a `PresentationModel` into an SVG `RenderedOutput`;
    register it with `@register_renderer`. You changed *nothing* about the visualization —
    because the model carries structure, not bytes, one model feeds every renderer.

??? success "Solution 2 — Kill the feed"
    An empty context yields a model with a warning; the renderer prints `UNAVAILABLE`. A
    `0.0` would tell an operator the fleet stopped — a lie they might act on. `UNAVAILABLE`
    is the honest, safe answer.

??? success "Solution 3 — Compose a dashboard"
    ```python
    dash = DashboardBuilder(owner="shift-a").add(kpi_widget).add(plan_widget).add(note_widget).build()
    for w in dash.widgets:
        RenderingPipeline(...).render(w, context=ctx)
    ```
    Three sources, three presentation models, one pipeline — no arithmetic in the dashboard.

??? success "Solution 4 — Export = live"
    Export re-renders the *same* `PresentationModel`s through the *same* pipeline, wrapped
    in an `ExportResult`. There is no second rendering path to drift, so the exported bytes
    match the live view by construction.

??? success "Solution 5 — Reflect on the chain"
    **The platform refuses to make a modelling/backend decision that depends on your
    site** — a forecaster, a causal model, a solver, a reasoning backend, a chart library.
    It defines a governed contract and lets a plugin supply the choice. A fabricated answer
    is worse than a governed refusal.

## 16. Further reading

- **[`visualization` package guide](../../packages/visualization.md)** — the capability-tour view.
- **[`visualization` API reference](../../api-reference/visualization.md)** — every symbol, from source.
- **[Visualization Design Specification](../../architecture/12_Visualization_Design_Specification.md)** · **[ADR-0012](../../adr/ADR-0012-Visualization.md)** — structure-not-bytes, the one pipeline, the no-charting-library rule.
- **[Fundamentals L10 — Visualization](../fundamentals/10_visualization.md)** · Package Tutorial [6 — KPIs](06_kpis.md).

---

## 🎉 You have finished the Package Tutorials

Thirteen deep tutorials across fourteen packages. You can now read *and extend*
every layer of MineProductivity — implement a repository, a KPI, a connector, a
forecaster, a twin, a simulation model, a solver, an agent, a renderer — because the
plugin-first architecture is now teachable end to end. Every refusal you met is an
extension point waiting for you.

- **[Package Tutorials index](../index.md)** · **[Architecture Handbook](../../architecture/README.md)**
