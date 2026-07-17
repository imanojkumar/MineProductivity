"""Lesson 10 -- Visualization: showing a human what the platform already knows.

This is the last package in the chain, and the one most likely to be
misunderstood. It does **no** business computation. It does not know what
a tonne is. It takes evidence the lower layers already governed -- a KPI
result, a trend, a recommendation -- and turns it into a structured
presentation.

Two design choices are worth understanding before you write a dashboard:

1. A `PresentationModel` carries **no rendered bytes**. It says "this is a
   KPI card titled PROD.TPH with value 1150" -- not "here is a PNG". That
   is what lets the same model render to text, SVG, HTML, or a PDF report
   without the platform ever depending on a charting library.
2. The package ships **zero** concrete visualizations and **zero**
   renderers. Both are interfaces. Your charting library lives in a
   plugin, never in the locked core.

Run: python examples/fundamentals/10_visualization/visualization.py
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
class ShiftKpiCard(Visualization):
    """Presents one governed KPI as a shift-handover headline card.

    Note what this does NOT do: it never computes tonnes/hours. It reads a
    KPIResult the KPI Engine already governed. Visualization presents; it
    does not derive (design spec 12 sec. 3.2).
    """

    meta = VisualizationMetadata(
        code="KPI_CARD.ShiftHandover",
        category=VisualizationCategory.KPI_CARD,
        description="A single-KPI headline card for shift handover.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        wanted = widget.binding.get("kpi_code", "")
        matched = [result for result in context.kpi_results if result.code == wanted]
        if not matched:
            # "Qualify, don't coerce" (sec. 30): missing evidence is a warning
            # on a real model -- never a crash, and never a fabricated zero.
            return PresentationModel(
                category=type(self).meta.category,
                title=wanted or widget.code,
                warnings=(f"no KPIResult for {wanted!r} in context",),
            )
        result = matched[0]
        return PresentationModel(
            category=type(self).meta.category,
            title=wanted,
            series={"value": result.value, "unit": result.unit},
            evidence_refs=(wanted,),
        )


@register_renderer
class ControlRoomTextRenderer(Renderer):
    """Renders a model as plain text for a control-room terminal.

    A real site would register an SVG or HTML renderer here instead. The
    charting library would be imported in THAT plugin -- never here.
    """

    meta = RendererMetadata(
        code="TEXT.ControlRoom", description="Renders a model to control-room text."
    )

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        value = model.series.get("value")
        unit = model.series.get("unit", "")
        if value is None:
            return RenderedOutput(
                format="text", payload=f"{model.title}: UNAVAILABLE", warnings=model.warnings
            )
        return RenderedOutput(
            format="text", payload=f"{model.title}: {value:,.1f} {unit}", warnings=model.warnings
        )


@register_renderer
class ModelInspectorRenderer(Renderer):
    """A renderer that emits the PresentationModel's *structure* rather than a
    picture -- used below to show what the model actually carries.

    This is the public way to observe a model: a renderer is exactly where one
    legitimately lands. `Visualization._render` is the extension point you
    implement, not an API you call -- the pipeline calls it for you.
    """

    meta = RendererMetadata(
        code="INSPECT.Model", description="Emits a presentation model's structure as text."
    )

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(
            format="text",
            payload=(
                f"category={model.category.value} | title={model.title!r} | "
                f"series={dict(model.series)} | evidence_refs={model.evidence_refs}"
            ),
            warnings=model.warnings,
        )


def main() -> None:
    print("--- 1. The evidence was governed by the layers below ---")
    context = VisualizationContext(
        kpi_results=(KPIResult(code="PROD.TPH", value=1_150.0, unit="t/h", n=14),)
    )
    print("context carries a PROD.TPH KPIResult of 1,150.0 t/h")
    print("(visualization did not compute it and could not -- it has no idea")
    print(" what a tonne or an operating hour is)")

    print()
    print("--- 2. A Widget binds a visualization type to the evidence it wants ---")
    widget = Widget(
        code="tph_card",
        visualization_code="KPI_CARD.ShiftHandover",
        binding={"kpi_code": "PROD.TPH"},
    )
    print(f"widget {widget.code!r} -> {widget.visualization_code!r} binding={dict(widget.binding)}")

    print()
    print("--- 3. One pipeline: visualization -> PresentationModel -> renderer ---")
    pipeline = RenderingPipeline(registry=REGISTRY, renderers=RENDERERS)
    output = pipeline.render(widget, context=context, renderer_code="TEXT.ControlRoom")
    print(f"format : {output.format!r}")
    print(f"payload: {output.payload!r}")

    print()
    print("--- 4. The intermediate model carries structure, not pixels ---")
    # The SAME widget + context, sent to a different renderer. Nothing about the
    # visualization changed -- only what the model was rendered into.
    inspected = pipeline.render(widget, context=context, renderer_code="INSPECT.Model")
    print(inspected.payload)
    print("(no bytes, no colours, no fonts. That is why the SAME model can go")
    print(" to a terminal, an SVG dashboard, or an exported PDF unchanged --")
    print(" two renderers above, one unchanged visualization.)")

    print()
    print("--- 5. Qualify, don't coerce: missing evidence is a warning ---")
    empty = pipeline.render(
        widget, context=VisualizationContext(), renderer_code="TEXT.ControlRoom"
    )
    print(f"payload : {empty.payload!r}")
    print(f"warnings: {empty.warnings}")
    print("(a control room that silently shows 0.0 t/h when the feed dies is")
    print(" dangerous. The platform says UNAVAILABLE and tells you why.)")

    print()
    print("--- 6. Everything above was example-local, by design ---")
    print("visualization ships ZERO concrete Visualizations and ZERO Renderers.")
    print("Both classes in this file are yours. A charting/templating library")
    print("would be imported in a plugin -- the locked package imports none,")
    print("and a test enforces that (ADR-0012).")

    print()
    print("--- The chain, end to end ---")
    print("  events      -> the immutable facts        (lesson 04)")
    print("  ontology    -> what those facts are about (lesson 05)")
    print("  kpis        -> the governed measurement   (lesson 06)")
    print("  analytics   -> is it drifting?            (lesson 07)")
    print("  decision    -> what should we do, and why (lesson 08)")
    print("  digital_twin-> what is true right now     (lesson 09)")
    print("  visualization-> show a human              (this lesson)")
    print("Each layer consumed the one below and re-derived nothing. That")
    print("discipline is the whole architecture, and now you can read it.")


if __name__ == "__main__":
    main()
