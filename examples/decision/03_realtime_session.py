"""``RealTimeDecisionSession`` over a live ``events.EventBus``: each
published cycle event refreshes that equipment's ``PROD.TPH`` through
the real ``KPIEngine`` and re-runs the decision pipeline -- ``latest()``
then serves the per-scope result without re-running anything.

The session composes ``kpis.KPIEngine``/``analytics.BatchAnalyticsRunner``
rather than recomputing facts itself (design spec 07 sec. 3.2); with a
single fresh observation per event, the trend runner legitimately
declines (too few observations) and the pipeline decides on KPI
evidence alone.

Run: python examples/decision/03_realtime_session.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from _evidence import SHIFT_ID, build_engine, load_event_store

from mineproductivity.analytics import (
    AnalyticsContext,
    AnalyticsPipeline,
    BatchAnalyticsRunner,
    LinearTrendModel,
)
from mineproductivity.analytics import ModelStage as AnalyticsModelStage
from mineproductivity.core import PredicateSpecification
from mineproductivity.decision import (
    DecisionAuditTrail,
    DecisionContext,
    DecisionPipeline,
    ModelStage,
    Policy,
    Recommendation,
    RealTimeDecisionSession,
    Rule,
    RuleEngineStage,
    ThresholdDecisionStrategy,
)
from mineproductivity.events import CycleEvent, EventEnvelope, EventID, EventMetadata, EventVersion
from mineproductivity.events.bus import _InMemoryEventBus

TPH_TARGET = 210.0


def _cycle_envelope(equipment_id: str, event_time: datetime) -> EventEnvelope[CycleEvent]:
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=CycleEvent(
            equipment_id=equipment_id,
            shift_id=SHIFT_ID,
            queue_min=10.0,
            spot_min=5.0,
            load_min=15.0,
            haul_min=20.0,
            dump_min=5.0,
            return_min=5.0,
            payload_t=225.0,
        ),
        event_time_utc=event_time,
        processing_time_utc=event_time,
        ingestion_time_utc=event_time,
        metadata=EventMetadata(name="cycle", source_system="dispatch"),
    )


def main() -> None:
    print("--- 1. One shared pipeline: throughput policy over PROD.TPH ---")
    rules: dict[str, Rule] = {
        "tph_below_target": PredicateSpecification(
            lambda ctx: any(r.value is not None and r.value < TPH_TARGET for r in ctx.kpi_results)
        ),
    }
    policy = Policy(code="PROD.LowTruckThroughput", rules=rules, strategy_code="STRATEGY.Threshold")
    pipeline = DecisionPipeline(
        stages=(
            RuleEngineStage(policy=policy),
            ModelStage(ThresholdDecisionStrategy(policy=policy, severity="medium")),
        )
    )

    print()
    print("--- 2. A session subscribed to the bus, composing the real engines ---")
    store = load_event_store()
    trail = DecisionAuditTrail()
    bus: _InMemoryEventBus = _InMemoryEventBus()
    session = RealTimeDecisionSession(
        bus=bus,
        pipeline=pipeline,
        kpi_engine=build_engine(store),
        analytics_runner=BatchAnalyticsRunner(
            pipeline=AnalyticsPipeline(stages=(AnalyticsModelStage(LinearTrendModel()),)),
            context=AnalyticsContext(event_store=store),
        ),
        kpi_codes=("PROD.TPH",),
        window="shift",
        audit_trail=trail,
    )
    subscription = session.start()
    print(f"subscribed: {type(subscription).__name__}")

    print()
    print("--- 3. Publish cycle events; each one refreshes and re-decides its scope ---")
    event_time = datetime(2026, 6, 25, 17, 30, tzinfo=timezone.utc)
    for equipment_id in ("HT-214", "HT-215"):
        bus.publish(_cycle_envelope(equipment_id, event_time))

    print()
    print("--- 4. latest() serves each scope's result without re-running the pipeline ---")
    for equipment_id in ("HT-214", "HT-215"):
        scope = {"equipment_id": equipment_id, "shift": SHIFT_ID}
        latest = session.latest(scope)
        assert latest is not None
        if isinstance(latest, Recommendation):
            print(f"{equipment_id}: RECOMMEND -> {latest.summary}")
        else:
            print(f"{equipment_id}: no action (no rule triggered, tph at/above target)")

    print()
    print("--- 5. Real-time/batch parity: the same context, decided the same way ---")
    engine = build_engine(store)
    tph = engine.execute(
        "PROD.TPH", window="shift", scope={"equipment_id": "HT-215", "shift": SHIFT_ID}
    ).unwrap()
    context = DecisionContext(
        kpi_results=(tph,),
        analytics_results=(),
        scope={"equipment_id": "HT-215", "shift": SHIFT_ID},
    )
    batch_result = pipeline.run(context).unwrap()
    realtime_result = session.latest({"equipment_id": "HT-215", "shift": SHIFT_ID})
    assert isinstance(batch_result, Recommendation)
    assert isinstance(realtime_result, Recommendation)
    print(f"batch:     {batch_result.triggered_rules} {batch_result.summary!r}")
    print(f"real-time: {realtime_result.triggered_rules} {realtime_result.summary!r}")

    print()
    print("--- 6. Every actionable run was audited, traceable to its source event ---")
    for entry in trail.query():
        scope_text = dict(entry.context_scope)
        print(
            f"{entry.result.model_code} for {scope_text}"
            f" <- event(s) {[event_id[:8] + '...' for event_id in entry.source_event_ids]}"
        )

    subscription.cancel()
    print()
    print("--- 7. Cancelled: later events no longer update the session ---")
    bus.publish(_cycle_envelope("HT-216", event_time))
    print(f"HT-216 after cancel: {session.latest({'equipment_id': 'HT-216', 'shift': SHIFT_ID})}")


if __name__ == "__main__":
    main()
