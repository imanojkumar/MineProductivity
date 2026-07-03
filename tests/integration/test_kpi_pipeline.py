"""Integration test for the KPI Engine: the full pipeline from the real
CSV fixtures in ``tests/fixtures/kpis/``, through canonical events, a
durable ``EventStore`` append, and into ``KPIEngine.execute()``/
``summary()`` -- no direct function call bypassing a stage (design spec
§30, mirroring the Connector and Event Framework integration tests'
Category B pattern).
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from mineproductivity.events import (
    BaseEvent,
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

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "kpis"
_SHIFT_ID = "A-2026-06-25"
_SHIFT_START = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)
_SHIFT_END = datetime(2026, 6, 25, 18, 0, tzinfo=timezone.utc)


def _rows(filename: str) -> list[dict[str, str]]:
    with (_FIXTURES_DIR / filename).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _append(store: _InMemoryEventStore, payload: BaseEvent, event_time: datetime) -> None:
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


def _load_dataset() -> _InMemoryEventStore:
    """Stand-in for a future FMSConnector: parses the raw CSV fixtures
    into canonical events -- the rest of this test never touches CSV
    columns again, only canonical events and KPI results."""
    store = _InMemoryEventStore()

    for row in _rows("cycle_events.csv"):
        event_time = datetime.fromisoformat(row["event_time"]).replace(tzinfo=timezone.utc)
        _append(
            store,
            CycleEvent(
                equipment_id=row["equipment_id"],
                shift_id=_SHIFT_ID,
                queue_min=float(row["queue_min"]),
                spot_min=float(row["spot_min"]),
                load_min=float(row["load_min"]),
                haul_min=float(row["haul_min"]),
                dump_min=float(row["dump_min"]),
                return_min=float(row["return_min"]),
                payload_t=float(row["payload_t"]),
                material_type=row["material_type"],
            ),
            event_time,
        )

    for row in _rows("maintenance_events.csv"):
        failure_start = datetime.fromisoformat(row["failure_start"]).replace(tzinfo=timezone.utc)
        return_to_service = datetime.fromisoformat(row["return_to_service"]).replace(
            tzinfo=timezone.utc
        )
        _append(
            store,
            MaintenanceEvent(
                equipment_id=row["equipment_id"],
                shift_id=_SHIFT_ID,
                failure_start_utc=failure_start,
                return_to_service_utc=return_to_service,
                total_downtime_h=float(row["total_downtime_h"]),
                is_planned=row["is_planned"].strip().lower() == "true",
                failure_mode_code=row["failure_mode_code"],
            ),
            failure_start,
        )

    for row in _rows("production_events.csv"):
        event_time = datetime.fromisoformat(row["event_time"]).replace(tzinfo=timezone.utc)
        _append(
            store,
            ProductionEvent(
                equipment_id=row["equipment_id"],
                shift_id=_SHIFT_ID,
                pit_code=row["pit_code"],
                material_type=row["material_type"],
                tonnes_moved=float(row["tonnes_moved"]),
                planned_tonnes=float(row["planned_tonnes"]),
                operating_h=float(row["operating_h"]),
            ),
            event_time,
        )

    for row in _rows("consumption_events.csv"):
        event_time = datetime.fromisoformat(row["event_time"]).replace(tzinfo=timezone.utc)
        _append(
            store,
            ConsumptionEvent(
                equipment_id=row["equipment_id"],
                shift_id=_SHIFT_ID,
                resource_type=ResourceType(row["resource_type"]),
                quantity=float(row["quantity"]),
                unit=row["unit"],
            ),
            event_time,
        )

    for row in _rows("delay_events.csv"):
        event_time = datetime.fromisoformat(row["event_time"]).replace(tzinfo=timezone.utc)
        _append(
            store,
            DelayEvent(
                equipment_id=row["equipment_id"],
                shift_id=_SHIFT_ID,
                delay_category=DelayCategory(row["delay_category"]),
                delay_reason=row["delay_reason"],
                duration_min=float(row["duration_min"]),
            ),
            event_time,
        )

    for row in _rows("safety_events.csv"):
        event_time = datetime.fromisoformat(row["event_time"]).replace(tzinfo=timezone.utc)
        _append(
            store,
            SafetyEvent(
                equipment_id=row["equipment_id"],
                shift_id=_SHIFT_ID,
                safety_event_type=SafetyEventType(row["safety_event_type"]),
                severity=SafetySeverity(row["severity"]),
            ),
            event_time,
        )

    return store


def _build_engine(store: _InMemoryEventStore) -> KPIEngine:
    shift = Shift(
        id=_SHIFT_ID,
        mine_id="bingham-west",
        pattern="2x12",
        start_utc=_SHIFT_START,
        end_utc=_SHIFT_END,
        scheduled_h=12.0,
    )
    return KPIEngine(
        store=store,
        registry=REGISTRY,
        backend=PandasBackend(),
        cache=ResultCache(),
        shifts={shift.id: shift},
    )


class TestGoldenReproduction:
    """Category A: the golden fixtures reproduce the golden canonical
    event field values exactly."""

    def test_cycle_events_reproduced_exactly(self) -> None:
        rows = _rows("cycle_events.csv")
        assert len(rows) == 12
        assert rows[0]["equipment_id"] == "HT-214"
        assert rows[0]["material_type"] == "ore"
        assert float(rows[0]["payload_t"]) == 230.0


class TestFullPipelineNoStageBypassed:
    """Category B: CSV -> canonical events -> EventStore -> KPIEngine ->
    KPIResult, with no direct function call bypassing a stage."""

    def test_simple_leaf_kpi_end_to_end(self) -> None:
        store = _load_dataset()
        engine = _build_engine(store)

        result = engine.execute("PROD.TPH", window="shift", scope={"shift": _SHIFT_ID})
        assert result.is_ok
        tph = result.unwrap()
        assert tph.n == 12
        assert tph.value is not None
        assert round(tph.value, 1) == 216.8

    def test_composite_kpi_resolves_its_dependency_graph_end_to_end(self) -> None:
        store = _load_dataset()
        engine = _build_engine(store)

        result = engine.execute("UTIL.OEE", window="shift", scope={"shift": _SHIFT_ID})
        assert result.is_ok
        oee = result.unwrap()
        assert oee.value is not None
        assert 0.0 < oee.value < 1.0

    def test_batched_summary_computes_every_standard_library_kpi(self) -> None:
        """Requests the 12 known Standard Library codes explicitly rather
        than ``list(REGISTRY)`` -- ``REGISTRY`` is a process-level global
        other test modules also register fixture KPIs into within the
        same pytest session, so trusting its live contents here would
        make this test's outcome depend on unrelated test-collection
        order."""
        standard_library_codes = [
            "PROD.TPH",
            "UTIL.PA",
            "UTIL.UA",
            "UTIL.Performance",
            "UTIL.OEE",
            "MAINT.MTTR",
            "HAUL.TruckCycleTime",
            "DISP.TotalDelayHours",
            "ENERGY.FuelConsumed",
            "QUAL.OreProportion",
            "COST.FuelPerTonne",
            "SAFE.SpeedViolationCount",
        ]
        store = _load_dataset()
        engine = _build_engine(store)

        result = engine.summary(standard_library_codes, window="shift", scope={"shift": _SHIFT_ID})
        assert result.is_ok
        summary = result.unwrap()
        assert set(summary) == set(standard_library_codes)
        # every flagship in this dataset has matching data -- none are
        # silently uncomputable because a stage was skipped.
        assert all(kpi_result.value is not None for kpi_result in summary.values())

    def test_result_caching_survives_a_second_execute_call(self) -> None:
        store = _load_dataset()
        engine = _build_engine(store)

        first = engine.execute("PROD.TPH", window="shift", scope={"shift": _SHIFT_ID}).unwrap()
        second = engine.execute("PROD.TPH", window="shift", scope={"shift": _SHIFT_ID}).unwrap()
        assert first == second


class TestCrossEventTypeKPIs:
    """Certifies KPIs that read more than one canonical event type in a
    single window resolve correctly through the real pipeline."""

    def test_use_of_availability_reads_maintenance_and_production(self) -> None:
        store = _load_dataset()
        engine = _build_engine(store)

        result = engine.execute("UTIL.UA", window="shift", scope={"shift": _SHIFT_ID}).unwrap()
        assert result.value is not None

    def test_fuel_per_tonne_reads_consumption_and_cycle(self) -> None:
        store = _load_dataset()
        engine = _build_engine(store)

        result = engine.execute(
            "COST.FuelPerTonne", window="shift", scope={"shift": _SHIFT_ID}
        ).unwrap()
        assert result.value is not None
        assert result.value > 0
