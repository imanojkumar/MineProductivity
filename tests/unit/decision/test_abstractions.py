"""Tests for mineproductivity.decision.abstractions."""

from __future__ import annotations

import concurrent.futures
from typing import ClassVar

import pytest

from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.kpis import KPIResult

from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
from mineproductivity.decision.result import DecisionResult


class _StubModel(DecisionModel):
    meta: ClassVar[DecisionMetadata] = DecisionMetadata(
        code="STRATEGY.Stub",
        category=DecisionCategory.STRATEGY,
        description="test-only",
    )

    def __init__(self) -> None:
        self.decide_calls = 0

    def _decide(self, context: DecisionContext) -> DecisionResult:
        self.decide_calls += 1
        return DecisionResult(model_code=self.meta.code)


def _kpi_result(value: float = 1.0) -> KPIResult:
    return KPIResult(code="PROD.TPH", value=value, unit="t/h")


class TestDecisionContext:
    def test_construction_with_kpi_results(self) -> None:
        context = DecisionContext(
            kpi_results=(_kpi_result(),), analytics_results=(), scope={"pit": "north"}
        )
        assert context.kpi_results == (_kpi_result(),)
        assert context.scope == {"pit": "north"}
        assert context.event_store is None
        assert context.as_of is None

    def test_sequences_are_normalized_to_tuples(self) -> None:
        context = DecisionContext(kpi_results=[_kpi_result()], analytics_results=[], scope={})
        assert isinstance(context.kpi_results, tuple)
        assert isinstance(context.analytics_results, tuple)

    def test_optional_event_store(self) -> None:
        store = _InMemoryEventStore()
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={}, event_store=store)
        assert context.event_store is store

    def test_repr_includes_class_name(self) -> None:
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        assert "DecisionContext" in repr(context)

    def test_triggered_rules_defaults_to_none(self) -> None:
        """None means 'no RuleEngineStage has run yet' -- deliberately
        distinct from () ('ran, found nothing'); see this field's own
        docstring for why collapsing the two would be a bug."""
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        assert context.triggered_rules is None

    def test_triggered_rules_is_normalized_to_a_tuple(self) -> None:
        context = DecisionContext(
            kpi_results=(), analytics_results=(), scope={}, triggered_rules=["a", "b"]
        )
        assert context.triggered_rules == ("a", "b")

    def test_explicit_empty_triggered_rules_is_preserved_as_empty_not_none(self) -> None:
        context = DecisionContext(
            kpi_results=(), analytics_results=(), scope={}, triggered_rules=()
        )
        assert context.triggered_rules == ()
        assert context.triggered_rules is not None

    def test_triggered_rules_is_mutable_in_place(self) -> None:
        """Phase 07.2's RuleEngineStage relies on being able to attach
        its result to an existing context without reconstructing it --
        DecisionContext is a plain, mutable bundle (unlike the frozen
        DecisionResult family), consistent with its Phase 07.1 shape."""
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        context.triggered_rules = ("low_oee",)
        assert context.triggered_rules == ("low_oee",)

    def test_repr_includes_triggered_rules(self) -> None:
        context = DecisionContext(
            kpi_results=(), analytics_results=(), scope={}, triggered_rules=("low_oee",)
        )
        assert "low_oee" in repr(context)

    def test_recommendations_defaults_to_none(self) -> None:
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        assert context.recommendations is None

    def test_recommendations_is_normalized_to_a_tuple(self) -> None:
        from mineproductivity.decision.result import Recommendation

        rec = Recommendation(
            policy_code="X", triggered_rules=("a",), summary="x", severity="low", evidence=()
        )
        context = DecisionContext(
            kpi_results=(), analytics_results=(), scope={}, recommendations=[rec]
        )
        assert context.recommendations == (rec,)

    def test_explicit_empty_recommendations_is_preserved_as_empty_not_none(self) -> None:
        context = DecisionContext(
            kpi_results=(), analytics_results=(), scope={}, recommendations=()
        )
        assert context.recommendations == ()
        assert context.recommendations is not None

    def test_recommendations_is_mutable_in_place(self) -> None:
        from mineproductivity.decision.result import Recommendation

        rec = Recommendation(
            policy_code="X", triggered_rules=("a",), summary="x", severity="low", evidence=()
        )
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        context.recommendations = (rec,)
        assert context.recommendations == (rec,)

    def test_repr_includes_recommendations(self) -> None:
        from mineproductivity.decision.result import Recommendation

        rec = Recommendation(
            policy_code="AVAIL.LowFleetAvailability",
            triggered_rules=("a",),
            summary="x",
            severity="low",
            evidence=(),
        )
        context = DecisionContext(
            kpi_results=(), analytics_results=(), scope={}, recommendations=(rec,)
        )
        assert "AVAIL.LowFleetAvailability" in repr(context)


class TestDecisionModel:
    def test_cannot_instantiate_abstract_base_directly(self) -> None:
        with pytest.raises(TypeError):
            DecisionModel()  # type: ignore[abstract]

    def test_decide_delegates_to_decide_impl_when_evidence_present(self) -> None:
        model = _StubModel()
        context = DecisionContext(kpi_results=(_kpi_result(),), analytics_results=(), scope={})

        result = model.decide(context)

        assert model.decide_calls == 1
        assert result.model_code == "STRATEGY.Stub"
        assert result.warnings == ()

    def test_decide_returns_warning_result_without_calling_decide_impl_when_no_evidence(
        self,
    ) -> None:
        model = _StubModel()
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})

        result = model.decide(context)

        assert model.decide_calls == 0
        assert result.model_code == "STRATEGY.Stub"
        assert len(result.warnings) == 1
        assert "no evidence in context" in result.warnings[0]

    def test_analytics_results_alone_is_sufficient_evidence(self) -> None:
        from mineproductivity.analytics import AnalyticsResult

        model = _StubModel()
        context = DecisionContext(
            kpi_results=(),
            analytics_results=(AnalyticsResult(model_code="TREND.Linear"),),
            scope={},
        )

        result = model.decide(context)

        assert model.decide_calls == 1
        assert result.model_code == "STRATEGY.Stub"


class TestDecisionModelStatelessConcurrency:
    """``DecisionModel``'s own class docstring: 'every subclass MUST be
    stateless across decide() calls... so a single instance is safe to
    share and invoke concurrently from multiple threads.' Proven here
    against a purely functional model whose result depends only on its
    per-call input, so a data race would show up as a wrong result for
    one of the concurrent calls."""

    def test_shared_instance_produces_correct_independent_results_under_concurrent_decide(
        self,
    ) -> None:
        class _EchoModel(DecisionModel):
            meta: ClassVar[DecisionMetadata] = DecisionMetadata(
                code="STRATEGY.Echo", category=DecisionCategory.STRATEGY, description="x"
            )

            def _decide(self, context: DecisionContext) -> DecisionResult:
                total = sum(result.value or 0.0 for result in context.kpi_results)
                return DecisionResult(model_code=f"total={total}")

        model = _EchoModel()

        def _context_for(value: float) -> DecisionContext:
            return DecisionContext(
                kpi_results=(_kpi_result(value),), analytics_results=(), scope={}
            )

        values = [float(i) for i in range(1, 21)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(model.decide, _context_for(value)) for value in values]
            results = [future.result() for future in futures]

        for value, result in zip(values, results, strict=True):
            assert result.model_code == f"total={value}"
