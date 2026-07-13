"""Benchmark scenario: multi-widget render throughput, sequential vs.
parallel, at representative widget counts (Visualization implementation
checklist, Benchmarks). A dashboard's widgets each render through one
``RenderingPipeline.render`` call; a busy wall-board re-renders many
widgets per refresh.

``Visualization``/``Renderer`` instances are stateless and share no
mutable state across calls (design spec §29), so a dashboard's widget
renders parallelize across a thread pool. The example-local view and
renderer are trivial, isolating pipeline dispatch overhead from a real
charting backend's cost.

Standalone by design. Results are recorded in
``benchmark/reports/visualization/``.

Run: python benchmark/scenarios/visualization/render_parallel_throughput.py
"""

from __future__ import annotations

import platform
import time
from concurrent.futures import ThreadPoolExecutor

from mineproductivity.kpis import KPIResult
from mineproductivity.visualization import (
    REGISTRY,
    RENDERERS,
    PresentationModel,
    RenderedOutput,
    Renderer,
    RendererMetadata,
    RenderingPipeline,
    Visualization,
    VisualizationCategory,
    VisualizationContext,
    VisualizationMetadata,
    Widget,
    register,
    register_renderer,
)

WIDGET_COUNTS = (50, 200, 1_000)
WORKERS = 8


@register
class _BenchmarkCard(Visualization):
    meta = VisualizationMetadata(
        code="KPI_CARD.Benchmark",
        category=VisualizationCategory.KPI_CARD,
        description="Trivial KPI card isolating pipeline dispatch cost.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        value = context.kpi_results[0].value if context.kpi_results else 0.0
        return PresentationModel(
            category=type(self).meta.category, title=widget.code, series={"value": value}
        )


@register_renderer
class _BenchmarkRenderer(Renderer):
    meta = RendererMetadata(code="TEXT.Benchmark", description="Trivial text renderer.")

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(format="text", payload=f"{model.title}={model.series.get('value')}")


def _widgets(count: int) -> list[Widget]:
    return [
        Widget(code=f"w{index}", visualization_code="KPI_CARD.Benchmark") for index in range(count)
    ]


def _context() -> VisualizationContext:
    return VisualizationContext(kpi_results=(KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),))


def _sequential(
    pipeline: RenderingPipeline, widgets: list[Widget], ctx: VisualizationContext
) -> float:
    start = time.perf_counter()
    for widget in widgets:
        pipeline.render(widget, context=ctx, renderer_code="TEXT.Benchmark")
    return time.perf_counter() - start


def _parallel(
    pipeline: RenderingPipeline, widgets: list[Widget], ctx: VisualizationContext
) -> float:
    def _one(widget: Widget) -> RenderedOutput:
        return pipeline.render(widget, context=ctx, renderer_code="TEXT.Benchmark")

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(_one, widgets))
    return time.perf_counter() - start


def main() -> None:
    print("Visualization multi-widget render throughput (sequential vs. parallel)")
    print(f"python={platform.python_version()} machine={platform.machine()} workers={WORKERS}")
    print()
    print(f"{'widgets':>8} {'seq_ms':>10} {'seq_per_s':>12} {'par_ms':>10} {'par_per_s':>12}")

    pipeline = RenderingPipeline(registry=REGISTRY, renderers=RENDERERS)
    ctx = _context()
    for count in WIDGET_COUNTS:
        widgets = _widgets(count)
        seq_seconds = _sequential(pipeline, widgets, ctx)
        par_seconds = _parallel(pipeline, widgets, ctx)
        print(
            f"{count:>8} {seq_seconds * 1e3:>10.2f} {count / seq_seconds:>12.0f}"
            f" {par_seconds * 1e3:>10.2f} {count / par_seconds:>12.0f}"
        )


if __name__ == "__main__":
    main()
