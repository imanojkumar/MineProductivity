"""The design spec §15 multi-source worked example, end-to-end: a
built ``Dashboard`` whose three widgets each present a *different lower
layer's already-structured output* — a KPI card, an optimization
plan-comparison view, and an agent-explanation note — rendered
independently through the one ``RenderingPipeline``. ``visualization``
reads evidence assembled by the caller; it never re-derives a KPI, a
plan, or an agent decision (spec 12 §3.2).

All concrete visualizations and the renderer are example-local.

Run: python examples/visualization/02_multi_source_dashboard.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.agents import AgentAuditEntry, AgentResult
from mineproductivity.decision import Explanation
from mineproductivity.kpis import KPIResult
from mineproductivity.optimization import OptimizationResult
from mineproductivity.visualization import (
    REGISTRY,
    RENDERERS,
    DashboardBuilder,
    Layout,
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

WHEN = datetime(2026, 7, 12, tzinfo=timezone.utc)


@register
class KpiCard(Visualization):
    meta = VisualizationMetadata(
        code="KPI_CARD.Multi",
        category=VisualizationCategory.KPI_CARD,
        description="A KPI headline card.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        wanted = widget.binding.get("kpi_code", "")
        matched = [r for r in context.kpi_results if r.code == wanted]
        if not matched:
            return PresentationModel(
                category=type(self).meta.category,
                title=wanted,
                warnings=(f"no KPIResult for {wanted!r}",),
            )
        return PresentationModel(
            category=type(self).meta.category,
            title=wanted,
            series={"value": matched[0].value},
            evidence_refs=(wanted,),
        )


@register
class PlanComparisonView(Visualization):
    meta = VisualizationMetadata(
        code="OPTIMIZATION_COMPARISON.Multi",
        category=VisualizationCategory.OPTIMIZATION_COMPARISON,
        description="A solved-plan comparison view.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        return PresentationModel(
            category=type(self).meta.category,
            title="Plan comparison",
            series={
                "objective_values": tuple(r.objective_value for r in context.optimization_results)
            },
            evidence_refs=tuple(r.run_id for r in context.optimization_results),
        )


@register
class AgentNote(Visualization):
    meta = VisualizationMetadata(
        code="AGENT_EXPLANATION.Multi",
        category=VisualizationCategory.AGENT_EXPLANATION,
        description="An agent-explanation handover note.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        premises: tuple[str, ...] = ()
        for entry in context.agent_audit_entries:
            if entry.result.explanation is not None:
                premises += entry.result.explanation.premises
        return PresentationModel(
            category=type(self).meta.category,
            title="Handover note",
            series={"premises": premises},
            evidence_refs=tuple(entry.agent_code for entry in context.agent_audit_entries),
        )


@register_renderer
class TextRenderer(Renderer):
    meta = RendererMetadata(code="TEXT.Multi", description="Renders a model to plain text.")

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(format="text", payload=f"{model.title} :: {dict(model.series)}")


def main() -> None:
    print("--- 1. Build a dashboard from three different-source widgets ---")
    dashboard = (
        DashboardBuilder(owner="shift-supervisor-a")
        .with_name("Night Shift Handover")
        .with_widget(
            Widget(
                code="tph_card",
                visualization_code="KPI_CARD.Multi",
                binding={"kpi_code": "PROD.TPH"},
            )
        )
        .with_widget(
            Widget(code="plan_compare", visualization_code="OPTIMIZATION_COMPARISON.Multi")
        )
        .with_widget(Widget(code="agent_note", visualization_code="AGENT_EXPLANATION.Multi"))
        .with_layout(
            Layout(
                code="handover_grid",
                slots={
                    "tph_card": "row=1;col=1",
                    "plan_compare": "row=1;col=2",
                    "agent_note": "row=2;col=1;span=2",
                },
            )
        )
        .with_theme("DARK_HIGH_CONTRAST")
        .build()
    )
    print(f"dashboard id={dashboard.id} owner={dashboard.owner!r} widgets={len(dashboard.widgets)}")

    print()
    print("--- 2. Assemble evidence from three lower layers (caller's job) ---")
    context = VisualizationContext(
        kpi_results=(KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),),
        optimization_results=(OptimizationResult(run_id="OPT-2026-041", objective_value=51_500.0),),
        agent_audit_entries=(
            AgentAuditEntry(
                recorded_at=WHEN,
                result=AgentResult(
                    task_id="TASK-1",
                    explanation=Explanation(
                        premises=("Reassign two trucks to the north pit",),
                        evidence_refs=("OPT-2026-041",),
                    ),
                ),
                agent_code="SHIFT_SUPERVISOR.HandoverAdvisor",
                scope={},
            ),
        ),
    )

    print()
    print("--- 3. Render each widget independently through the one pipeline ---")
    pipeline = RenderingPipeline(registry=REGISTRY, renderers=RENDERERS)
    for widget in dashboard.widgets:
        output = pipeline.render(widget, context=context, renderer_code="TEXT.Multi")
        print(f"  {widget.code}: {output.payload}")


if __name__ == "__main__":
    main()
