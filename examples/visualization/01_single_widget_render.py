"""A single widget rendered end-to-end through ``RenderingPipeline``
(design spec §11): a registered ``Visualization`` produces a
backend-independent ``PresentationModel``, a registered ``Renderer``
turns it into a ``RenderedOutput`` — the one and only rendering code
path. The "qualify, don't coerce" rule (§30) is shown too: missing
evidence surfaces as a warning, never a raise.

Both the concrete visualization and renderer are example-local: the
package ships zero of either by design (interface-only extension
points, spec 12 §3.1, §4, ADR-0012).

Run: python examples/visualization/01_single_widget_render.py
"""

from __future__ import annotations

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


@register
class KpiHeadlineCard(Visualization):
    """Presents one KPI as a headline card (example-local, stateless)."""

    meta = VisualizationMetadata(
        code="KPI_CARD.Headline",
        category=VisualizationCategory.KPI_CARD,
        description="A single-KPI headline card.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        wanted = widget.binding.get("kpi_code", "")
        matched = [result for result in context.kpi_results if result.code == wanted]
        if not matched:
            return PresentationModel(
                category=type(self).meta.category,
                title=wanted or widget.code,
                warnings=(f"no KPIResult for {wanted!r} in context",),
            )
        return PresentationModel(
            category=type(self).meta.category,
            title=wanted,
            series={"value": matched[0].value, "unit": matched[0].unit},
            evidence_refs=(wanted,),
        )


@register_renderer
class TextRenderer(Renderer):
    """Renders a presentation model to plain text (example-local)."""

    meta = RendererMetadata(code="TEXT.Console", description="Renders a model to plain text.")

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        value = model.series.get("value")
        unit = model.series.get("unit", "")
        payload = f"{model.title}: {value} {unit}".strip() if value is not None else model.title
        return RenderedOutput(format="text", payload=payload, warnings=model.warnings)


def main() -> None:
    pipeline = RenderingPipeline(registry=REGISTRY, renderers=RENDERERS)
    widget = Widget(
        code="tph_card", visualization_code="KPI_CARD.Headline", binding={"kpi_code": "PROD.TPH"}
    )

    print("--- 1. Render with the evidence present ---")
    context = VisualizationContext(
        kpi_results=(KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),)
    )
    output = pipeline.render(widget, context=context, renderer_code="TEXT.Console")
    print(f"format={output.format!r} payload={output.payload!r} warnings={output.warnings}")

    print()
    print("--- 2. Render with the evidence missing: qualify, don't coerce (sec. 30) ---")
    empty = pipeline.render(widget, context=VisualizationContext(), renderer_code="TEXT.Console")
    print(f"payload={empty.payload!r} warnings={empty.warnings}")


if __name__ == "__main__":
    main()
