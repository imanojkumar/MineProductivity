"""Shared sample-dataset loader for the ``examples/kpis/`` scripts.

Not part of the public API -- every example script imports this module
to build the same one-shift ``KPIEngine`` against the golden fixtures in
``tests/fixtures/kpis/``, so each script can focus on demonstrating one
engine capability rather than repeating CSV-parsing boilerplate.
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

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "kpis"

SHIFT_ID = "A-2026-06-25"
SHIFT_START = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)
SHIFT_END = datetime(2026, 6, 25, 18, 0, tzinfo=timezone.utc)


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


def _rows(filename: str) -> list[dict[str, str]]:
    with (FIXTURES_DIR / filename).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_event_store() -> _InMemoryEventStore:
    """Parse every CSV fixture in ``tests/fixtures/kpis/`` into canonical
    events and append them to a fresh, in-memory ``EventStore`` -- the
    same shift's cycles, downtime, production plan, fuel burn, delay, and
    a safety observation, all for shift ``A-2026-06-25``."""
    store = _InMemoryEventStore()

    for row in _rows("cycle_events.csv"):
        event_time = datetime.fromisoformat(row["event_time"]).replace(tzinfo=timezone.utc)
        _append(
            store,
            CycleEvent(
                equipment_id=row["equipment_id"],
                shift_id=SHIFT_ID,
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
                shift_id=SHIFT_ID,
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
                shift_id=SHIFT_ID,
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
                shift_id=SHIFT_ID,
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
                shift_id=SHIFT_ID,
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
                shift_id=SHIFT_ID,
                safety_event_type=SafetyEventType(row["safety_event_type"]),
                severity=SafetySeverity(row["severity"]),
            ),
            event_time,
        )

    return store


def build_shift() -> Shift:
    return Shift(
        id=SHIFT_ID,
        mine_id="bingham-west",
        pattern="2x12",
        start_utc=SHIFT_START,
        end_utc=SHIFT_END,
        scheduled_h=12.0,
    )


def build_engine() -> KPIEngine:
    """The one-liner every example script calls: a real ``KPIEngine``
    wired to the sample dataset's ``EventStore``, the full Standard
    Library ``REGISTRY``, the default ``PandasBackend``, and a fresh
    ``ResultCache``."""
    shift = build_shift()
    return KPIEngine(
        store=load_event_store(),
        registry=REGISTRY,
        backend=PandasBackend(),
        cache=ResultCache(),
        shifts={shift.id: shift},
    )
