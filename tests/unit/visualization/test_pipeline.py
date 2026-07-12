"""Tests for mineproductivity.visualization.pipeline (design spec
§11): the exact dispatch sequence, the qualify-don't-coerce warning
flow, the §15 multi-source worked example, and the §29 concurrency
contract."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

from mineproductivity.agents import AgentAuditEntry, AgentResult
from mineproductivity.decision import Explanation
from mineproductivity.kpis import KPIResult
from mineproductivity.optimization import OptimizationResult
from mineproductivity.visualization._registry import (
    REGISTRY,
    RENDERERS,
    register,
    register_renderer,
)
from mineproductivity.visualization.abstractions import (
    Visualization,
    VisualizationCategory,
    VisualizationContext,
    VisualizationMetadata,
)
from mineproductivity.visualization.dashboard_builder import DashboardBuilder
from mineproductivity.visualization.exceptions import DashboardNotFoundError, RenderingError
from mineproductivity.visualization.layout import Layout
from mineproductivity.visualization.pipeline import RenderingPipeline
from mineproductivity.visualization.presentation import PresentationModel
from mineproductivity.visualization.renderer import (
    RenderedOutput,
    Renderer,
    RendererMetadata,
)
from mineproductivity.visualization.widget import Widget

_WHEN = datetime(2026, 7, 8, tzinfo=timezone.utc)


@register
class _PipelineKpiCard(Visualization):
    meta = VisualizationMetadata(
        code="KPI_CARD.PipelineFixture",
        category=VisualizationCategory.KPI_CARD,
        description="A KPI headline card for pipeline tests.",
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
            series={"value": matched[0].value},
            evidence_refs=(wanted,),
        )


@register
class _PipelinePlanCompare(Visualization):
    meta = VisualizationMetadata(
        code="OPTIMIZATION_COMPARISON.PipelineFixture",
        category=VisualizationCategory.OPTIMIZATION_COMPARISON,
        description="A solved-plan comparison view for pipeline tests.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        return PresentationModel(
            category=type(self).meta.category,
            title="Plan comparison",
            series={
                "objective_values": tuple(
                    result.objective_value for result in context.optimization_results
                )
            },
            evidence_refs=tuple(result.run_id for result in context.optimization_results),
        )


@register
class _PipelineAgentNote(Visualization):
    meta = VisualizationMetadata(
        code="AGENT_EXPLANATION.PipelineFixture",
        category=VisualizationCategory.AGENT_EXPLANATION,
        description="An agent-explanation view for pipeline tests.",
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


@register
class _PipelineRaising(Visualization):
    meta = VisualizationMetadata(
        code="CHART.PipelineRaisingFixture",
        category=VisualizationCategory.CHART,
        description="Raises for a structurally valid input.",
    )

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        raise RuntimeError("backend exploded")


@register_renderer
class _TextRenderer(Renderer):
    meta = RendererMetadata(
        code="TEXT.PipelineFixture", description="Renders a model to plain text."
    )

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(
            format="text",
            payload=f"text::{model.title}",
            warnings=model.warnings,
        )


@register_renderer
class _MarkdownRenderer(Renderer):
    meta = RendererMetadata(code="MD.PipelineFixture", description="Renders a model to Markdown.")

    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        return RenderedOutput(format="markdown", payload=f"# {model.title}")


def _pipeline() -> RenderingPipeline:
    return RenderingPipeline(registry=REGISTRY, renderers=RENDERERS)


def _kpi_widget() -> Widget:
    return Widget(
        code="tph_card",
        visualization_code="KPI_CARD.PipelineFixture",
        binding={"kpi_code": "PROD.TPH"},
    )


def _context() -> VisualizationContext:
    return VisualizationContext(kpi_results=(KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),))


class TestDispatchSequence:
    def test_dispatches_to_exactly_the_named_visualization_and_renderer(self) -> None:
        """Design spec §33: never a different registered type."""
        pipeline = _pipeline()
        text = pipeline.render(
            _kpi_widget(), context=_context(), renderer_code="TEXT.PipelineFixture"
        )
        markdown = pipeline.render(
            _kpi_widget(), context=_context(), renderer_code="MD.PipelineFixture"
        )
        assert text == RenderedOutput(format="text", payload="text::PROD.TPH")
        assert markdown == RenderedOutput(format="markdown", payload="# PROD.TPH")

    def test_unknown_visualization_code_raises(self) -> None:
        with pytest.raises(DashboardNotFoundError, match="Visualization"):
            _pipeline().render(
                Widget(code="w", visualization_code="KPI_CARD.NeverRegistered"),
                context=_context(),
                renderer_code="TEXT.PipelineFixture",
            )

    def test_unknown_renderer_code_raises(self) -> None:
        with pytest.raises(DashboardNotFoundError, match="Renderer"):
            _pipeline().render(_kpi_widget(), context=_context(), renderer_code="NEVER.Registered")

    def test_a_raising_backend_surfaces_as_rendering_error(self) -> None:
        with pytest.raises(RenderingError, match="backend exploded"):
            _pipeline().render(
                Widget(code="w", visualization_code="CHART.PipelineRaisingFixture"),
                context=_context(),
                renderer_code="TEXT.PipelineFixture",
            )

    def test_repr(self) -> None:
        assert "RenderingPipeline" in repr(_pipeline())


class TestQualifyDontCoerce:
    def test_incomplete_evidence_flows_through_as_a_warning_never_a_raise(self) -> None:
        """Design spec §30's central rule, end to end through both
        dispatch hops."""
        output = _pipeline().render(
            _kpi_widget(),
            context=VisualizationContext(),
            renderer_code="TEXT.PipelineFixture",
        )
        assert output.warnings == ("no KPIResult for 'PROD.TPH' in context",)


class TestMultiSourceWorkedExample:
    def test_design_spec_15_dashboard_renders_each_widget_independently(self) -> None:
        """The §15 worked example shape: KPI_CARD +
        OPTIMIZATION_COMPARISON + AGENT_EXPLANATION widgets on one
        built dashboard."""
        widgets = (
            _kpi_widget(),
            Widget(
                code="plan_compare",
                visualization_code="OPTIMIZATION_COMPARISON.PipelineFixture",
                binding={"run_id": "OPT-2026-041"},
            ),
            Widget(
                code="agent_note",
                visualization_code="AGENT_EXPLANATION.PipelineFixture",
                binding={"agent_code": "SHIFT_SUPERVISOR.HandoverAdvisor"},
            ),
        )
        dashboard = (
            DashboardBuilder(owner="shift-supervisor-a")
            .with_name("Night Shift Handover")
            .with_widget(widgets[0])
            .with_widget(widgets[1])
            .with_widget(widgets[2])
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
        context = VisualizationContext(
            kpi_results=(KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),),
            optimization_results=(
                OptimizationResult(run_id="OPT-2026-041", objective_value=51_500.0),
            ),
            agent_audit_entries=(
                AgentAuditEntry(
                    recorded_at=_WHEN,
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
        pipeline = _pipeline()
        outputs = [
            pipeline.render(widget, context=context, renderer_code="TEXT.PipelineFixture")
            for widget in dashboard.widgets
        ]
        assert [output.payload for output in outputs] == [
            "text::PROD.TPH",
            "text::Plan comparison",
            "text::Handover note",
        ]
        assert all(output.warnings == () for output in outputs)


class TestConcurrency:
    def test_independent_widget_renders_execute_fully_in_parallel(self) -> None:
        """Design spec §29: no shared mutable state across calls."""
        pipeline = _pipeline()
        contexts = [
            VisualizationContext(
                kpi_results=(KPIResult(code="PROD.TPH", value=float(i), unit="t/h"),)
            )
            for i in range(16)
        ]

        def _one(context: VisualizationContext) -> RenderedOutput:
            return pipeline.render(
                _kpi_widget(), context=context, renderer_code="TEXT.PipelineFixture"
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            outputs = list(pool.map(_one, contexts))
        assert len(outputs) == 16
        assert all(output.payload == "text::PROD.TPH" for output in outputs)
