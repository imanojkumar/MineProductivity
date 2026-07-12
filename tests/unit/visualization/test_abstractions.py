"""Tests for mineproductivity.visualization.abstractions (design spec
§8, §26): the interface-only Visualization ABC, the metadata schema,
the caller-assembled context, and the per-category flagship
implementations with hand-computed expected PresentationModels (§17,
§33)."""

from __future__ import annotations

import inspect
from datetime import datetime, timezone

import pytest

import mineproductivity.visualization.abstractions as abstractions_module
from mineproductivity.agents import AgentAuditEntry, AgentResult
from mineproductivity.analytics import AnalyticsResult
from mineproductivity.decision import DecisionResult, Explanation
from mineproductivity.digital_twin import TwinSnapshot, TwinState, TwinStatus
from mineproductivity.events import AsOf
from mineproductivity.kpis import KPIResult
from mineproductivity.optimization import OptimizationResult
from mineproductivity.simulation import SimulationResult, SimulationState
from mineproductivity.visualization.abstractions import (
    Visualization,
    VisualizationCategory,
    VisualizationContext,
    VisualizationMetadata,
)
from mineproductivity.visualization.exceptions import VisualizationValidationError
from mineproductivity.visualization.presentation import PresentationModel
from mineproductivity.visualization.widget import Widget

_WHEN = datetime(2026, 7, 8, tzinfo=timezone.utc)


def _meta(code: str, category: VisualizationCategory) -> VisualizationMetadata:
    return VisualizationMetadata(code=code, category=category, description="Flagship fixture.")


def _widget(visualization_code: str, **binding: str) -> Widget:
    return Widget(code="fixture", visualization_code=visualization_code, binding=binding)


class TestVisualizationCategory:
    def test_exactly_the_eight_closed_members(self) -> None:
        assert {member.value for member in VisualizationCategory} == {
            "chart",
            "graph",
            "kpi_card",
            "timeline",
            "simulation_playback",
            "digital_twin_view",
            "optimization_comparison",
            "agent_explanation",
        }


class TestVisualizationMetadata:
    def test_name_defaults_to_code(self) -> None:
        assert _meta("KPI_CARD.Standard", VisualizationCategory.KPI_CARD).name == (
            "KPI_CARD.Standard"
        )

    def test_empty_code_raises(self) -> None:
        with pytest.raises(VisualizationValidationError, match="code"):
            _meta("  ", VisualizationCategory.KPI_CARD)

    def test_non_category_raises(self) -> None:
        with pytest.raises(VisualizationValidationError, match="category"):
            VisualizationMetadata(code="X", category="chart", description="x")  # type: ignore[arg-type]


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            Visualization()  # type: ignore[abstract]

    def test_render_is_the_one_shared_abstract_method(self) -> None:
        assert Visualization.__abstractmethods__ == frozenset({"_render"})

    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(abstractions_module, inspect.isclass):
            if issubclass(obj, Visualization):
                assert inspect.isabstract(obj)


class TestVisualizationContext:
    def test_every_evidence_field_defaults_empty(self) -> None:
        context = VisualizationContext()
        assert context.kpi_results == ()
        assert context.analytics_results == ()
        assert context.decision_results == ()
        assert context.twin_snapshot is None
        assert context.simulation_results == ()
        assert context.optimization_results == ()
        assert context.agent_audit_entries == ()

    def test_sequences_are_coerced_to_tuples_once_at_construction(self) -> None:
        source = [KPIResult(code="PROD.TPH", value=1212.1, unit="t/h")]
        context = VisualizationContext(kpi_results=source)
        source.append(KPIResult(code="PROD.TPH", value=0.0, unit="t/h"))
        assert len(context.kpi_results) == 1

    def test_repr_names_all_seven_evidence_fields(self) -> None:
        rendered = repr(VisualizationContext())
        for field in (
            "kpi_results",
            "analytics_results",
            "decision_results",
            "twin_snapshot",
            "simulation_results",
            "optimization_results",
            "agent_audit_entries",
        ):
            assert field in rendered


class TestStatelessness:
    def test_a_conforming_visualization_mutates_no_instance_attribute(self) -> None:
        """Design spec §29: statefulness lives entirely in Dashboard."""

        class _Stateless(Visualization):
            meta = _meta("KPI_CARD.StatelessFixture", VisualizationCategory.KPI_CARD)

            def _render(
                self, widget: Widget, *, context: VisualizationContext
            ) -> PresentationModel:
                return PresentationModel(category=type(self).meta.category, title=widget.code)

        visualization = _Stateless()
        before = dict(getattr(visualization, "__dict__", {}))
        visualization._render(_widget("KPI_CARD.StatelessFixture"), context=VisualizationContext())
        assert dict(getattr(visualization, "__dict__", {})) == before


class _KpiCardFlagship(Visualization):
    meta = _meta("KPI_CARD.Flagship", VisualizationCategory.KPI_CARD)

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        wanted = widget.binding.get("kpi_code", "")
        matched = [result for result in context.kpi_results if result.code == wanted]
        if not matched:
            return PresentationModel(
                category=type(self).meta.category,
                title=wanted,
                warnings=(f"no KPIResult for {wanted!r} in context",),
            )
        return PresentationModel(
            category=type(self).meta.category,
            title=wanted,
            series={"value": matched[0].value, "unit": matched[0].unit},
            evidence_refs=(wanted,),
        )


class _ChartFlagship(Visualization):
    meta = _meta("CHART.Flagship", VisualizationCategory.CHART)

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        return PresentationModel(
            category=type(self).meta.category,
            title="Analytics chart",
            series={"models": tuple(r.model_code for r in context.analytics_results)},
            evidence_refs=tuple(r.model_code for r in context.analytics_results),
        )


class _GraphFlagship(Visualization):
    meta = _meta("GRAPH.Flagship", VisualizationCategory.GRAPH)

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        return PresentationModel(
            category=type(self).meta.category,
            title="Decision graph",
            series={"nodes": tuple(r.model_code for r in context.decision_results)},
            evidence_refs=tuple(r.model_code for r in context.decision_results),
        )


class _TimelineFlagship(Visualization):
    meta = _meta("TIMELINE.Flagship", VisualizationCategory.TIMELINE)

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        return PresentationModel(
            category=type(self).meta.category,
            title="KPI timeline",
            series={"events": tuple(r.code for r in context.kpi_results)},
            evidence_refs=tuple(r.code for r in context.kpi_results),
        )


class _SimulationPlaybackFlagship(Visualization):
    meta = _meta("SIMULATION_PLAYBACK.Flagship", VisualizationCategory.SIMULATION_PLAYBACK)

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        trajectory = tuple(
            result.final_state.simulated_time.isoformat() for result in context.simulation_results
        )
        return PresentationModel(
            category=type(self).meta.category,
            title="Simulation playback",
            series={"trajectory": trajectory},
        )


class _DigitalTwinViewFlagship(Visualization):
    meta = _meta("DIGITAL_TWIN_VIEW.Flagship", VisualizationCategory.DIGITAL_TWIN_VIEW)

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        if context.twin_snapshot is None:
            return PresentationModel(
                category=type(self).meta.category,
                title="Twin view",
                warnings=("no TwinSnapshot in context",),
            )
        return PresentationModel(
            category=type(self).meta.category,
            title=context.twin_snapshot.twin_id,
            series=dict(context.twin_snapshot.state.attributes),
        )


class _OptimizationComparisonFlagship(Visualization):
    meta = _meta("OPTIMIZATION_COMPARISON.Flagship", VisualizationCategory.OPTIMIZATION_COMPARISON)

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        return PresentationModel(
            category=type(self).meta.category,
            title="Plan comparison",
            series={
                "objective_values": tuple(r.objective_value for r in context.optimization_results)
            },
            evidence_refs=tuple(r.run_id for r in context.optimization_results),
        )


class _AgentExplanationFlagship(Visualization):
    meta = _meta("AGENT_EXPLANATION.Flagship", VisualizationCategory.AGENT_EXPLANATION)

    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        premises: tuple[str, ...] = ()
        for entry in context.agent_audit_entries:
            if entry.result.explanation is not None:
                premises += entry.result.explanation.premises
        return PresentationModel(
            category=type(self).meta.category,
            title="Agent explanation",
            series={"premises": premises},
            evidence_refs=tuple(e.agent_code for e in context.agent_audit_entries),
        )


def _full_context() -> VisualizationContext:
    return VisualizationContext(
        kpi_results=(KPIResult(code="PROD.TPH", value=1212.1, unit="t/h"),),
        analytics_results=(AnalyticsResult(model_code="TREND.Linear"),),
        decision_results=(DecisionResult(model_code="STRATEGY.Threshold"),),
        twin_snapshot=TwinSnapshot(
            twin_id="CONV-7",
            state=TwinState(attributes={"belt_speed_mps": 3.1}, captured_at=_WHEN),
            status=TwinStatus.SYNCHRONIZED,
            as_of=AsOf(utc=_WHEN),
        ),
        simulation_results=(
            SimulationResult(
                final_state=SimulationState(attributes={"tph": 1180.0}, simulated_time=_WHEN)
            ),
        ),
        optimization_results=(OptimizationResult(run_id="OPT-2026-041", objective_value=51_500.0),),
        agent_audit_entries=(
            AgentAuditEntry(
                recorded_at=_WHEN,
                result=AgentResult(
                    task_id="TASK-1",
                    explanation=Explanation(
                        premises=("OEE below 0.65",), evidence_refs=("UTIL.OEE",)
                    ),
                ),
                agent_code="SHIFT_SUPERVISOR.HandoverAdvisor",
                scope={},
            ),
        ),
    )


class TestFlagshipCategories:
    """Design spec §33: one flagship per category, each with a
    hand-computed expected PresentationModel; §17: each
    domain-specific category binds exactly the context field its own
    name implies."""

    def test_kpi_card_reads_kpi_results(self) -> None:
        model = _KpiCardFlagship()._render(
            _widget("KPI_CARD.Flagship", kpi_code="PROD.TPH"), context=_full_context()
        )
        assert model == PresentationModel(
            category=VisualizationCategory.KPI_CARD,
            title="PROD.TPH",
            series={"value": 1212.1, "unit": "t/h"},
            evidence_refs=("PROD.TPH",),
        )

    def test_chart_reads_analytics_results(self) -> None:
        model = _ChartFlagship()._render(_widget("CHART.Flagship"), context=_full_context())
        assert model.series["models"] == ("TREND.Linear",)
        assert model.evidence_refs == ("TREND.Linear",)

    def test_graph_reads_decision_results(self) -> None:
        model = _GraphFlagship()._render(_widget("GRAPH.Flagship"), context=_full_context())
        assert model.series["nodes"] == ("STRATEGY.Threshold",)

    def test_timeline_reads_kpi_results_in_order(self) -> None:
        model = _TimelineFlagship()._render(_widget("TIMELINE.Flagship"), context=_full_context())
        assert model.series["events"] == ("PROD.TPH",)

    def test_simulation_playback_reads_simulation_results_never_optimization(self) -> None:
        model = _SimulationPlaybackFlagship()._render(
            _widget("SIMULATION_PLAYBACK.Flagship"),
            context=VisualizationContext(
                simulation_results=_full_context().simulation_results,
                optimization_results=_full_context().optimization_results,
            ),
        )
        assert model.series["trajectory"] == (_WHEN.isoformat(),)
        empty = _SimulationPlaybackFlagship()._render(
            _widget("SIMULATION_PLAYBACK.Flagship"),
            context=VisualizationContext(optimization_results=_full_context().optimization_results),
        )
        assert empty.series["trajectory"] == ()  # optimization evidence is never read

    def test_digital_twin_view_reads_the_twin_snapshot(self) -> None:
        model = _DigitalTwinViewFlagship()._render(
            _widget("DIGITAL_TWIN_VIEW.Flagship"), context=_full_context()
        )
        assert model.title == "CONV-7"
        assert model.series["belt_speed_mps"] == 3.1

    def test_optimization_comparison_reads_optimization_results(self) -> None:
        model = _OptimizationComparisonFlagship()._render(
            _widget("OPTIMIZATION_COMPARISON.Flagship"), context=_full_context()
        )
        assert model.series["objective_values"] == (51_500.0,)
        assert model.evidence_refs == ("OPT-2026-041",)

    def test_agent_explanation_reads_agent_audit_entries(self) -> None:
        model = _AgentExplanationFlagship()._render(
            _widget("AGENT_EXPLANATION.Flagship"), context=_full_context()
        )
        assert model.series["premises"] == ("OEE below 0.65",)
        assert model.evidence_refs == ("SHIFT_SUPERVISOR.HandoverAdvisor",)

    def test_incomplete_evidence_qualifies_with_a_warning_never_raises(self) -> None:
        """Design spec §30's central rule."""
        model = _KpiCardFlagship()._render(
            _widget("KPI_CARD.Flagship", kpi_code="PROD.TPH"),
            context=VisualizationContext(),
        )
        assert model.warnings == ("no KPIResult for 'PROD.TPH' in context",)
