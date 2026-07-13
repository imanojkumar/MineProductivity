# Examples — mineproductivity.visualization

## Purpose

Runnable, minimal, self-contained scripts demonstrating the Visualization package — the platform's final layer: a single widget render, a multi-source dashboard, an exported report, a simulation-playback view, and a third-party visualization+renderer plugin. Every concrete visualization and renderer in these scripts is example-local — the package ships zero of either by design (`Visualization`/`Renderer` are interface-only extension points, design spec §3.1, §4, ADR-0012).

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/visualization/` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the Visualization public API.
- Serve as executable documentation that stays correct because it is actually run.
- Demonstrate the platform disciplines end-to-end: one `RenderingPipeline` code path for live and exported output; "qualify, don't coerce" (missing evidence becomes a warning, never a raise); and presentation of every lower layer's already-structured output (KPIs, plans, agent explanations, simulation frames) without ever re-deriving it.

## Contents

- `01_single_widget_render.py` — one widget rendered through `RenderingPipeline` (visualization → `PresentationModel` → renderer → `RenderedOutput`), including the "qualify, don't coerce" warning path.
- `02_multi_source_dashboard.py` — the design spec §15 worked example: a built `Dashboard` with KPI-card, optimization-comparison, and agent-explanation widgets, each rendered independently.
- `03_export_report.py` — `ReportBuilder` composes the pipeline into a multi-section `Report`; an `ExportResult` wraps an ordinary `pipeline.render` call, proving one rendering code path for live and exported output (§33).
- `04_simulation_playback.py` — a `SIMULATION_PLAYBACK` view presenting a sequence of `simulation.SimulationResult` frames handed in on the context.
- `05_plugin_visualization_and_renderer.py` — a third-party-style `Visualization` and `Renderer` registered via entry points into the two orthogonal registries (`REGISTRY` for views, `RENDERERS` for renderers, design spec §22, §31), mirroring `examples/registry/01_register_and_discover.py`'s real-discovery pattern.

## Dependencies

`mineproductivity`, editable-installed (`pip install -e .`). No third-party charting/templating libraries are needed — the example renderers emit plain text/SVG strings, exactly the backend boundary the package keeps out of its own code. No network access.

## Running the Examples

```bash
pip install -e .
python examples/visualization/01_single_widget_render.py
python examples/visualization/02_multi_source_dashboard.py
python examples/visualization/03_export_report.py
python examples/visualization/04_simulation_playback.py
python examples/visualization/05_plugin_visualization_and_renderer.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add a `DIGITAL_TWIN_VIEW` and a `GRAPH` walkthrough once first-party or third-party visualization/renderer plugins implementing those interface-only extension points exist (deliberately never shipped inside `visualization` itself, design spec §3.1, §4).

## References

- [`docs/architecture/12_Visualization_Design_Specification.md`](../../docs/architecture/12_Visualization_Design_Specification.md) §8, §10–§11, §14–§15, §17–§19, §22, §26, §31
- [`src/mineproductivity/visualization/README.md`](../../src/mineproductivity/visualization/README.md)
- [`docs/adr/ADR-0012-Visualization.md`](../../docs/adr/ADR-0012-Visualization.md)
