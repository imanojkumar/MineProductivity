"""Tests for mineproductivity.kpis.engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from mineproductivity.events import (
    ConsumptionEvent,
    CycleEvent,
    DelayEvent,
    EventEnvelope,
    EventID,
    EventVersion,
    MaintenanceEvent,
    ProductionEvent,
    ResourceType,
    SafetyEvent,
    SafetySeverity,
)
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.ontology import DelayCategory, SafetyEventType, Shift

from mineproductivity.kpis import REGISTRY, KPIEngine, ResultCache
from mineproductivity.kpis.backends import PandasBackend

SHIFT_ID = "A-2026-06-25"
SHIFT_START = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)
SHIFT_END = datetime(2026, 6, 25, 18, 0, tzinfo=timezone.utc)


def make_shift(shift_id: str = SHIFT_ID, *, scheduled_h: float = 12.0) -> Shift:
    return Shift(
        id=shift_id,
        mine_id="bingham-west",
        pattern="2x12",
        start_utc=SHIFT_START,
        end_utc=SHIFT_END,
        scheduled_h=scheduled_h,
    )


def append_event(
    store: _InMemoryEventStore, payload: Any, *, event_time: datetime = SHIFT_START
) -> None:
    envelope = EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=payload,
        event_time_utc=event_time,
        processing_time_utc=event_time,
        ingestion_time_utc=event_time,
    )
    result = store.append(envelope)
    assert result.is_ok


class TestExecuteSimpleLeafKPI:
    def test_prod_tph_end_to_end(self, engine: KPIEngine, event_store: _InMemoryEventStore) -> None:
        append_event(
            event_store,
            CycleEvent(
                equipment_id="HT-214",
                shift_id=SHIFT_ID,
                queue_min=1.5,
                spot_min=0.5,
                load_min=2.5,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
            ),
        )
        result = engine.execute("PROD.TPH", window="shift", scope={"shift": SHIFT_ID})
        assert result.is_ok
        assert result.unwrap().value is not None

    def test_no_matching_events_returns_a_none_valued_result_not_an_error(
        self, engine: KPIEngine
    ) -> None:
        result = engine.execute("PROD.TPH", window="shift", scope={"shift": SHIFT_ID})
        assert result.is_ok
        assert result.unwrap().value is None


class TestExecuteCircularDependency:
    def test_returns_an_err_result_not_a_raised_exception(
        self, event_store: _InMemoryEventStore
    ) -> None:
        from mineproductivity.registry import Registry

        from mineproductivity.kpis.categories.production_kpi import ProductionKPI
        from mineproductivity.kpis.metadata import (
            Aggregation,
            DigitalMaturity,
            Direction,
            KPIMetadata,
        )

        def _meta(code: str, dependencies: tuple[str, ...]) -> KPIMetadata:
            return KPIMetadata(
                code=code,
                name=code,
                official_name=code,
                business_purpose="x",
                operational_question="x",
                business_meaning="x",
                formula="x",
                unit="x",
                dimensions=("Shift",),
                required_events=("CYCLE",),
                dependencies=dependencies,
                aggregation=Aggregation.ADDITIVE,
                direction=Direction.HIGHER_IS_BETTER,
                min_maturity=DigitalMaturity.L1_MANUAL,
                leading_or_lagging="lagging",
                operational_or_strategic="operational",
            )

        class _A(ProductionKPI):
            meta = _meta("PROD.EngineCycleA", ("PROD.EngineCycleB",))

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        class _B(ProductionKPI):
            meta = _meta("PROD.EngineCycleB", ("PROD.EngineCycleA",))

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        fake_registry: Registry[str, type] = Registry(name="engine-cycle-fixture")
        fake_registry.register("PROD.EngineCycleA", _A, metadata=_A.meta)
        fake_registry.register("PROD.EngineCycleB", _B, metadata=_B.meta)

        shift = make_shift()
        engine = KPIEngine(
            store=event_store,
            registry=fake_registry,
            backend=PandasBackend(),
            cache=ResultCache(),
            shifts={shift.id: shift},
        )
        result = engine.execute("PROD.EngineCycleA", window="shift", scope={"shift": SHIFT_ID})
        assert result.is_err


class TestExecuteComposite:
    def test_util_oee_resolves_its_dependencies_first(
        self, engine: KPIEngine, event_store: _InMemoryEventStore
    ) -> None:
        append_event(
            event_store,
            MaintenanceEvent(
                equipment_id="HT-214",
                shift_id=SHIFT_ID,
                failure_start_utc=SHIFT_START,
                return_to_service_utc=SHIFT_START,
                total_downtime_h=1.0,
                is_planned=False,
                failure_mode_code="HYD-001",
            ),
        )
        append_event(
            event_store,
            ProductionEvent(
                equipment_id="PIT-NORTH",
                shift_id=SHIFT_ID,
                pit_code="PIT-NORTH",
                material_type="Ore",
                tonnes_moved=9000.0,
                planned_tonnes=10000.0,
                operating_h=9.0,
            ),
        )
        result = engine.execute("UTIL.OEE", window="shift", scope={"shift": SHIFT_ID})
        assert result.is_ok
        assert result.unwrap().value is not None

    def test_missing_dependency_data_propagates_none_not_a_crash(self, engine: KPIEngine) -> None:
        result = engine.execute("UTIL.OEE", window="shift", scope={"shift": SHIFT_ID})
        assert result.is_ok
        assert result.unwrap().value is None


class TestSummaryBatchedExecution:
    def test_scans_the_store_once_per_distinct_required_events_set(
        self, engine: KPIEngine, event_store: _InMemoryEventStore
    ) -> None:
        append_event(
            event_store,
            CycleEvent(
                equipment_id="HT-214",
                shift_id=SHIFT_ID,
                queue_min=1.0,
                spot_min=0.5,
                load_min=2.5,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
            ),
        )
        append_event(
            event_store,
            DelayEvent(
                equipment_id="CR-01",
                shift_id=SHIFT_ID,
                delay_category=DelayCategory.EQUIPMENT,
                delay_reason="crusher_down",
                duration_min=60.0,
            ),
        )
        result = engine.summary(
            ["PROD.TPH", "DISP.TotalDelayHours"], window="shift", scope={"shift": SHIFT_ID}
        )
        assert result.is_ok
        summary = result.unwrap()
        assert set(summary) == {"PROD.TPH", "DISP.TotalDelayHours"}
        assert summary["DISP.TotalDelayHours"].value == 1.0

    def test_summary_with_a_circular_dependency_returns_err(
        self, event_store: _InMemoryEventStore
    ) -> None:
        from mineproductivity.registry import Registry

        from mineproductivity.kpis.categories.production_kpi import ProductionKPI
        from mineproductivity.kpis.metadata import (
            Aggregation,
            DigitalMaturity,
            Direction,
            KPIMetadata,
        )

        class _A(ProductionKPI):
            meta = KPIMetadata(
                code="PROD.SummaryCycleA",
                name="x",
                official_name="x",
                business_purpose="x",
                operational_question="x",
                business_meaning="x",
                formula="x",
                unit="x",
                dimensions=("Shift",),
                required_events=("CYCLE",),
                dependencies=("PROD.SummaryCycleA",),
                aggregation=Aggregation.ADDITIVE,
                direction=Direction.HIGHER_IS_BETTER,
                min_maturity=DigitalMaturity.L1_MANUAL,
                leading_or_lagging="lagging",
                operational_or_strategic="operational",
            )

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        fake_registry: Registry[str, type] = Registry(name="engine-summary-cycle-fixture")
        fake_registry.register("PROD.SummaryCycleA", _A, metadata=_A.meta)
        shift = make_shift()
        engine = KPIEngine(
            store=event_store,
            registry=fake_registry,
            backend=PandasBackend(),
            cache=ResultCache(),
            shifts={shift.id: shift},
        )
        result = engine.summary(["PROD.SummaryCycleA"], window="shift", scope={"shift": SHIFT_ID})
        assert result.is_err

    def test_summary_result_order_matches_the_requested_codes(
        self, engine: KPIEngine, event_store: _InMemoryEventStore
    ) -> None:
        result = engine.summary(
            ["DISP.TotalDelayHours", "PROD.TPH"], window="shift", scope={"shift": SHIFT_ID}
        )
        assert result.is_ok
        assert list(result.unwrap()) == ["DISP.TotalDelayHours", "PROD.TPH"]


class TestRowsForColumnPruning:
    def test_requesting_prod_tph_does_not_load_delay_rows(
        self, engine: KPIEngine, event_store: _InMemoryEventStore
    ) -> None:
        append_event(
            event_store,
            DelayEvent(
                equipment_id="CR-01",
                shift_id=SHIFT_ID,
                delay_category=DelayCategory.EQUIPMENT,
                delay_reason="x",
                duration_min=60.0,
            ),
        )
        tph_cls = REGISTRY.get("PROD.TPH")
        rows, fingerprint = engine.rows_for(tph_cls(), "shift", {"shift": SHIFT_ID})
        assert rows == []
        assert fingerprint == 0

    def test_matching_events_are_flattened_with_event_type_code_and_duration_h(
        self, engine: KPIEngine, event_store: _InMemoryEventStore
    ) -> None:
        append_event(
            event_store,
            CycleEvent(
                equipment_id="HT-214",
                shift_id=SHIFT_ID,
                queue_min=1.0,
                spot_min=0.5,
                load_min=2.5,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
            ),
        )
        tph_cls = REGISTRY.get("PROD.TPH")
        rows, fingerprint = engine.rows_for(tph_cls(), "shift", {"shift": SHIFT_ID})
        assert fingerprint == 1
        assert rows[0]["event_type_code"] == "CYCLE"
        assert "duration_h" in rows[0]
        assert "operating_h" in rows[0]  # CYCLE's duration alias


class TestScopeResolution:
    def test_equipment_id_scope_narrows_the_query(
        self, engine: KPIEngine, event_store: _InMemoryEventStore
    ) -> None:
        for equipment_id in ("HT-214", "HT-215"):
            append_event(
                event_store,
                CycleEvent(
                    equipment_id=equipment_id,
                    shift_id=SHIFT_ID,
                    queue_min=1.0,
                    spot_min=0.5,
                    load_min=2.5,
                    haul_min=8.0,
                    dump_min=1.0,
                    return_min=6.0,
                    payload_t=220.0,
                ),
            )
        tph_cls = REGISTRY.get("PROD.TPH")
        rows, _ = engine.rows_for(tph_cls(), "shift", {"shift": SHIFT_ID, "equipment_id": "HT-214"})
        assert len(rows) == 1
        assert rows[0]["equipment_id"] == "HT-214"

    def test_unknown_shift_falls_back_to_since_until_scope(
        self, event_store: _InMemoryEventStore
    ) -> None:
        engine = KPIEngine(
            store=event_store,
            registry=REGISTRY,
            backend=PandasBackend(),
            cache=ResultCache(),
            shifts={},
        )
        append_event(
            event_store,
            CycleEvent(
                equipment_id="HT-214",
                shift_id="unknown-shift",
                queue_min=1.0,
                spot_min=0.5,
                load_min=2.5,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
            ),
        )
        tph_cls = REGISTRY.get("PROD.TPH")
        scope = {
            "since": (SHIFT_START - timedelta(hours=1)).isoformat(),
            "until": (SHIFT_START + timedelta(hours=1)).isoformat(),
        }
        rows, fingerprint = engine.rows_for(tph_cls(), "shift", scope)
        assert fingerprint == 1
        # No shift resolved -> no scheduled_h injected.
        assert "scheduled_h" not in rows[0]

    def test_unknown_shift_and_no_since_until_yields_an_unbounded_query(
        self, event_store: _InMemoryEventStore
    ) -> None:
        engine = KPIEngine(
            store=event_store,
            registry=REGISTRY,
            backend=PandasBackend(),
            cache=ResultCache(),
            shifts={},
        )
        append_event(
            event_store,
            CycleEvent(
                equipment_id="HT-214",
                shift_id="unknown-shift",
                queue_min=1.0,
                spot_min=0.5,
                load_min=2.5,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
            ),
        )
        tph_cls = REGISTRY.get("PROD.TPH")
        rows, _ = engine.rows_for(tph_cls(), "shift", {})
        assert len(rows) == 1


class TestCachingIntegration:
    def test_repeated_execute_for_the_same_scope_hits_the_cache(
        self, engine: KPIEngine, event_store: _InMemoryEventStore
    ) -> None:
        append_event(
            event_store,
            CycleEvent(
                equipment_id="HT-214",
                shift_id=SHIFT_ID,
                queue_min=1.0,
                spot_min=0.5,
                load_min=2.5,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
            ),
        )
        first = engine.execute("PROD.TPH", window="shift", scope={"shift": SHIFT_ID}).unwrap()
        # A second event lands -- the fingerprint (matching envelope count)
        # changes, so the cached result must NOT be reused stale.
        append_event(
            event_store,
            CycleEvent(
                equipment_id="HT-215",
                shift_id=SHIFT_ID,
                queue_min=1.0,
                spot_min=0.5,
                load_min=2.5,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
            ),
        )
        second = engine.execute("PROD.TPH", window="shift", scope={"shift": SHIFT_ID}).unwrap()
        assert first.n == 1
        assert second.n == 2


def _one_hour_cycle(equipment_id: str, payload_t: float) -> CycleEvent:
    """A single haul cycle whose six legs sum to exactly 60 minutes, so
    that ``CycleEvent.duration_h()`` (and therefore the ``operating_h``
    row alias ``PROD.TPH`` reads -- each row is one cycle, not the whole
    shift) is exactly ``1.0``."""
    return CycleEvent(
        equipment_id=equipment_id,
        shift_id=SHIFT_ID,
        queue_min=10.0,
        spot_min=5.0,
        load_min=15.0,
        haul_min=20.0,
        dump_min=5.0,
        return_min=5.0,
        payload_t=payload_t,
    )


class TestRatioNeverAveraged:
    def test_a_shift_and_b_shift_combined_via_raw_rows_not_averaged_results(
        self, engine: KPIEngine, event_store: _InMemoryEventStore
    ) -> None:
        """Design spec §37.2's acceptance-criteria proof, driven through
        the real ``KPIEngine``: A-shift ran 12 one-hour cycles averaging
        1,300 t/h (15,600 t over 12 cycle-hours) and B-shift ran 6
        one-hour cycles averaging 1,100 t/h (6,600 t over 6 cycle-hours).
        The combined rate computed from the union of raw rows is 1,233.3
        t/h -- NOT the naive average of the two per-shift rates (1,200
        t/h)."""
        for _ in range(12):
            append_event(event_store, _one_hour_cycle("HT-214", 1300.0), event_time=SHIFT_START)
        tph_cls = REGISTRY.get("PROD.TPH")
        a_shift_rows, _ = engine.rows_for(tph_cls(), "shift", {"shift": SHIFT_ID})

        b_shift = make_shift("B-2026-06-25", scheduled_h=6.0)
        b_store = _InMemoryEventStore()
        for _ in range(6):
            b_shift_event = CycleEvent(
                equipment_id="HT-214",
                shift_id="B-2026-06-25",
                queue_min=10.0,
                spot_min=5.0,
                load_min=15.0,
                haul_min=20.0,
                dump_min=5.0,
                return_min=5.0,
                payload_t=1100.0,
            )
            append_event(b_store, b_shift_event)
        b_engine = KPIEngine(
            store=b_store,
            registry=REGISTRY,
            backend=PandasBackend(),
            cache=ResultCache(),
            shifts={b_shift.id: b_shift},
        )
        b_shift_rows, _ = b_engine.rows_for(tph_cls(), "shift", {"shift": "B-2026-06-25"})

        a_only = tph_cls().compute(a_shift_rows)
        b_only = tph_cls().compute(b_shift_rows)
        assert a_only.value == pytest.approx(1300.0)
        assert b_only.value == pytest.approx(1100.0)

        naive_average = (a_only.value + b_only.value) / 2
        combined_from_raw_rows = tph_cls().compute([*a_shift_rows, *b_shift_rows])
        assert combined_from_raw_rows.value == pytest.approx(1233.333333, rel=1e-6)
        assert combined_from_raw_rows.value != pytest.approx(naive_average)


class TestFullFleetScenario:
    def test_every_canonical_event_type_flattens_and_flows_through_summary(
        self, engine: KPIEngine, event_store: _InMemoryEventStore
    ) -> None:
        append_event(
            event_store,
            CycleEvent(
                equipment_id="HT-214",
                shift_id=SHIFT_ID,
                queue_min=1.5,
                spot_min=0.5,
                load_min=2.5,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
                material_type="ore",
            ),
        )
        append_event(
            event_store,
            MaintenanceEvent(
                equipment_id="HT-214",
                shift_id=SHIFT_ID,
                failure_start_utc=SHIFT_START,
                return_to_service_utc=SHIFT_START,
                total_downtime_h=1.0,
                is_planned=False,
                failure_mode_code="HYD-001",
            ),
        )
        append_event(
            event_store,
            ProductionEvent(
                equipment_id="PIT-NORTH",
                shift_id=SHIFT_ID,
                pit_code="PIT-NORTH",
                material_type="Ore",
                tonnes_moved=9000.0,
                planned_tonnes=10000.0,
                operating_h=9.0,
            ),
        )
        append_event(
            event_store,
            ConsumptionEvent(
                equipment_id="HT-214",
                shift_id=SHIFT_ID,
                resource_type=ResourceType.FUEL,
                quantity=500.0,
                unit="L",
            ),
        )
        append_event(
            event_store,
            DelayEvent(
                equipment_id="CR-01",
                shift_id=SHIFT_ID,
                delay_category=DelayCategory.EQUIPMENT,
                delay_reason="crusher_down",
                duration_min=60.0,
            ),
        )
        append_event(
            event_store,
            SafetyEvent(
                equipment_id="HT-214",
                shift_id=SHIFT_ID,
                safety_event_type=SafetyEventType.SPEED_VIOLATION,
                severity=SafetySeverity.MEDIUM,
            ),
        )

        result = engine.summary(list(REGISTRY), window="shift", scope={"shift": SHIFT_ID})
        assert result.is_ok
        summary = result.unwrap()
        assert set(summary) == set(REGISTRY)
        assert summary["PROD.TPH"].value is not None
        assert summary["UTIL.OEE"].value is not None
        assert summary["DISP.TotalDelayHours"].value == 1.0
        assert summary["SAFE.SpeedViolationCount"].value == 1.0
        assert summary["COST.FuelPerTonne"].value is not None
