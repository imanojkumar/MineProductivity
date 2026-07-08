"""Tests for mineproductivity.decision.realtime."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, ClassVar

from mineproductivity.analytics import AnalyticsResult
from mineproductivity.core import PredicateSpecification, Result
from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.audit import DecisionAuditTrail
from mineproductivity.decision.batch import BatchDecisionRunner
from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
from mineproductivity.decision.pipeline import DecisionPipeline, ModelStage, PipelineStage
from mineproductivity.decision.policy import Policy
from mineproductivity.decision.realtime import RealTimeDecisionSession
from mineproductivity.decision.result import DecisionResult, Recommendation
from mineproductivity.decision.rules import RuleEngineStage
from mineproductivity.decision.strategy import ThresholdDecisionStrategy
from mineproductivity.events.bus import _InMemoryEventBus
from mineproductivity.events.canonical import CycleEvent
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.identifier import EventID
from mineproductivity.events.versioning import EventVersion
from mineproductivity.kpis import KPIResult


class _Model(DecisionModel):
    meta: ClassVar[DecisionMetadata] = DecisionMetadata(
        code="STRATEGY.RealtimeTest", category=DecisionCategory.STRATEGY, description="x"
    )

    def _decide(self, context: DecisionContext) -> DecisionResult:
        return DecisionResult(model_code="TEST", warnings=("n=" + str(len(context.kpi_results)),))


class _AlwaysOkKPIEngine:
    def execute(self, code: str, *, window: str, scope: Any) -> Result[KPIResult]:
        return Result.ok(KPIResult(code=code, value=1.0, unit="t/h", scope=scope))


class _AlwaysErrKPIEngine:
    def execute(self, code: str, *, window: str, scope: Any) -> Result[KPIResult]:
        return Result.err("no data")


class _MixedKPIEngine:
    def execute(self, code: str, *, window: str, scope: Any) -> Result[KPIResult]:
        if code == "BAD.Code":
            return Result.err("no data")
        return Result.ok(KPIResult(code=code, value=1.0, unit="t/h", scope=scope))


class _AlwaysErrAnalyticsRunner:
    def run(self, series: Any) -> Result[AnalyticsResult]:
        return Result.err("not enough observations")


class _AlwaysOkAnalyticsRunner:
    def run(self, series: Any) -> Result[AnalyticsResult]:
        return Result.ok(AnalyticsResult(model_code="TREND.Fake"))


class _NoOpStage(PipelineStage):
    def process(self, context: DecisionContext) -> DecisionContext:
        return context


def _pipeline() -> DecisionPipeline:
    return DecisionPipeline(stages=(ModelStage(_Model()),))


def _envelope(
    *, equipment_id: str = "HT-1", shift_id: str = "A", event_time_utc: datetime | None = None
) -> EventEnvelope[CycleEvent]:
    now = event_time_utc or datetime(2026, 1, 1, tzinfo=timezone.utc)
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=CycleEvent(
            equipment_id=equipment_id,
            shift_id=shift_id,
            queue_min=1.0,
            spot_min=0.5,
            load_min=2.0,
            haul_min=8.0,
            dump_min=1.0,
            return_min=6.0,
            payload_t=220.0,
        ),
        event_time_utc=now,
        processing_time_utc=now,
        ingestion_time_utc=now,
        metadata=EventMetadata(name="cycle", source_system="test"),
    )


class TestRealTimeDecisionSessionLatestBeforeAnyEvent:
    def test_latest_returns_none_for_unknown_scope(self) -> None:
        session = RealTimeDecisionSession(
            bus=_InMemoryEventBus(),
            pipeline=_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        assert session.latest({"equipment_id": "HT-1", "shift": "A"}) is None


class TestRealTimeDecisionSessionOnEnvelope:
    def test_publish_refreshes_and_stores_a_result(self) -> None:
        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        session.start()
        bus.publish(_envelope())
        result = session.latest({"equipment_id": "HT-1", "shift": "A"})
        assert result is not None
        assert result.model_code == "TEST"

    def test_all_kpi_codes_failing_still_runs_the_pipeline_and_stores_its_result(self) -> None:
        """With zero refreshed KPIResults and no analytics evidence,
        DecisionModel.decide()'s own base orchestration (Phase 07.1)
        short-circuits before _Model._decide ever runs, returning its
        built-in 'no evidence' warning -- this session still runs the
        pipeline and stores whatever DecisionResult it produces, rather
        than special-casing the all-failed case itself."""
        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=_pipeline(),
            kpi_engine=_AlwaysErrKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        session.start()
        bus.publish(_envelope())
        result = session.latest({"equipment_id": "HT-1", "shift": "A"})
        assert result is not None
        assert result.warnings == (
            "no evidence in context: at least one KPIResult or AnalyticsResult required",
        )

    def test_partial_kpi_failure_keeps_the_successful_codes(self) -> None:
        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=_pipeline(),
            kpi_engine=_MixedKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH", "BAD.Code"),
            window="shift",
        )
        session.start()
        bus.publish(_envelope())
        result = session.latest({"equipment_id": "HT-1", "shift": "A"})
        assert result is not None
        assert result.warnings == ("n=1",)

    def test_analytics_runner_success_does_not_block_pipeline(self) -> None:
        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysOkAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        session.start()
        bus.publish(_envelope())
        result = session.latest({"equipment_id": "HT-1", "shift": "A"})
        assert result is not None
        assert result.model_code == "TEST"

    def test_failed_pipeline_run_leaves_latest_unset(self) -> None:
        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=DecisionPipeline(stages=(_NoOpStage(),)),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        session.start()
        bus.publish(_envelope())
        assert session.latest({"equipment_id": "HT-1", "shift": "A"}) is None

    def test_subscription_cancel_stops_further_updates(self) -> None:
        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        subscription = session.start()
        subscription.cancel()
        bus.publish(_envelope())
        assert session.latest({"equipment_id": "HT-1", "shift": "A"}) is None


class TestRealTimeDecisionSessionOutOfOrderDelivery:
    """Regression test for a race the phase's own QA review found: a
    handler's refresh work happens outside the lock, so an older
    envelope's slower-finishing handler could otherwise overwrite a
    newer envelope's already-stored result. ``_latest`` now stores each
    scope's ``event_time_utc`` alongside its ``DecisionResult`` and
    refuses to regress it."""

    def test_an_older_envelope_delivered_after_a_newer_one_does_not_regress_latest(self) -> None:
        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        session.start()
        newer = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        older = datetime(2026, 1, 1, 6, 0, tzinfo=timezone.utc)
        key = session._scope_key({"equipment_id": "HT-1", "shift": "A"})

        bus.publish(_envelope(event_time_utc=newer))
        assert session._latest[key][0] == newer

        bus.publish(_envelope(event_time_utc=older))
        assert session._latest[key][0] == newer

    def test_a_strictly_newer_envelope_still_overwrites(self) -> None:
        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        session.start()
        first = datetime(2026, 1, 1, 6, 0, tzinfo=timezone.utc)
        second = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        key = session._scope_key({"equipment_id": "HT-1", "shift": "A"})

        bus.publish(_envelope(event_time_utc=first))
        bus.publish(_envelope(event_time_utc=second))
        assert session._latest[key][0] == second


class TestRealTimeDecisionSessionScopeDerivation:
    def test_equipment_id_and_shift_are_both_present(self) -> None:
        scope = RealTimeDecisionSession._scope_for(_envelope(equipment_id="HT-9", shift_id="B"))
        assert dict(scope) == {"equipment_id": "HT-9", "shift": "B"}

    def test_missing_shift_id_attribute_omits_shift_key(self) -> None:
        fake_envelope = SimpleNamespace(payload=SimpleNamespace(equipment_id="HT-9"))
        scope = RealTimeDecisionSession._scope_for(fake_envelope)  # type: ignore[arg-type]
        assert dict(scope) == {"equipment_id": "HT-9"}

    def test_no_recognized_attributes_yields_empty_scope(self) -> None:
        fake_envelope = SimpleNamespace(payload=SimpleNamespace())
        scope = RealTimeDecisionSession._scope_for(fake_envelope)  # type: ignore[arg-type]
        assert dict(scope) == {}


class TestRealTimeDecisionSessionAuditTrail:
    def test_no_audit_trail_is_a_valid_default(self) -> None:
        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        session.start()
        bus.publish(_envelope())
        assert session.latest({"equipment_id": "HT-1", "shift": "A"}) is not None

    def test_successful_refresh_is_recorded_with_source_event_id(self) -> None:
        bus = _InMemoryEventBus()
        trail = DecisionAuditTrail()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
            audit_trail=trail,
        )
        session.start()
        envelope = _envelope()
        bus.publish(envelope)
        entries = trail.query()
        assert len(entries) == 1
        assert entries[0].source_event_ids == (envelope.event_id.value,)

    def test_failed_pipeline_run_is_not_recorded(self) -> None:
        bus = _InMemoryEventBus()
        trail = DecisionAuditTrail()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=DecisionPipeline(stages=(_NoOpStage(),)),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
            audit_trail=trail,
        )
        session.start()
        bus.publish(_envelope())
        assert trail.query() == ()


class TestRealTimeDecisionSessionRepr:
    def test_repr_includes_kpi_codes_and_window(self) -> None:
        session = RealTimeDecisionSession(
            bus=_InMemoryEventBus(),
            pipeline=_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        text = repr(session)
        assert "PROD.TPH" in text
        assert "shift" in text


class TestRealTimeBatchParity:
    """Design spec §34's real-time/batch parity acceptance proof:
    ``RealTimeDecisionSession.latest()`` and a ``BatchDecisionRunner``
    run over the same assembled ``DecisionContext`` produce the same
    ``DecisionResult`` -- the two execution modes are entry points into
    one shared ``DecisionPipeline.run()``, never two divergent decision
    paths. ``computed_at`` (a wall-clock construction timestamp) is
    normalized before comparison; every decision-bearing field
    (``policy_code``, ``triggered_rules``, ``summary``, ``severity``,
    ``evidence``, ``model_code``, ``warnings``) must match exactly."""

    def test_latest_equals_batch_run_over_the_same_assembled_context(self) -> None:
        policy = Policy(
            code="PROD.HighThroughput",
            rules={
                "tph_at_capacity": PredicateSpecification(
                    lambda ctx: any(r.value is not None and r.value >= 0.9 for r in ctx.kpi_results)
                )
            },
            strategy_code="STRATEGY.Threshold",
        )

        def make_pipeline() -> DecisionPipeline:
            return DecisionPipeline(
                stages=(
                    RuleEngineStage(policy=policy),
                    ModelStage(ThresholdDecisionStrategy(policy=policy, severity="high")),
                )
            )

        bus = _InMemoryEventBus()
        session = RealTimeDecisionSession(
            bus=bus,
            pipeline=make_pipeline(),
            kpi_engine=_AlwaysOkKPIEngine(),
            analytics_runner=_AlwaysErrAnalyticsRunner(),
            kpi_codes=("PROD.TPH",),
            window="shift",
        )
        session.start()
        bus.publish(_envelope())
        scope = {"equipment_id": "HT-1", "shift": "A"}
        realtime_result = session.latest(scope)
        assert isinstance(realtime_result, Recommendation)

        # The same assembled context the session built internally:
        # _AlwaysOkKPIEngine's output for each kpi_code, no analytics
        # (the runner errs), the envelope-derived scope.
        kpi_result = _AlwaysOkKPIEngine().execute("PROD.TPH", window="shift", scope=scope)
        context = DecisionContext(
            kpi_results=(kpi_result.unwrap(),), analytics_results=(), scope=scope
        )
        batch_outcome = BatchDecisionRunner(pipeline=make_pipeline()).run(context)
        assert batch_outcome.is_ok
        batch_result = batch_outcome.unwrap()
        assert isinstance(batch_result, Recommendation)

        fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert realtime_result.replace(computed_at=fixed) == batch_result.replace(computed_at=fixed)
