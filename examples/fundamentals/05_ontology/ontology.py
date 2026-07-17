"""Lesson 05 -- Ontology: agreeing what a 'truck' is before you measure one.

Two sites that define "haul truck" differently cannot compare their
tonnes-per-hour, no matter how good their arithmetic is. The ontology is
the platform's shared, typed, machine-readable vocabulary: equipment,
locations, organisation, materials. Every package above it models the
mine using *these* concepts, so a KPI computed at one pit means the same
thing at another.

Run: python examples/fundamentals/05_ontology/ontology.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from mineproductivity.ontology import (
    Bench,
    Fleet,
    HydraulicShovel,
    Mine,
    OperationalState,
    Pit,
    Relationship,
    RelationshipKind,
    RigidHaulTruck,
    Shift,
)


def main() -> None:
    print("--- 1. Equipment is a typed leaf, not a string in a spreadsheet ---")
    truck = RigidHaulTruck(
        id="HT-214",
        model="CAT 793F",
        fuel_type="diesel",
        fleet_id="FL-NORTH",
        rated_capacity=226.0,  # nominal payload of a 793F (the 797F is ~363 t)
    )
    shovel = HydraulicShovel(id="SH-1", model="EX8000", fleet_id="FL-NORTH", rated_capacity=42.0)
    print(f"{truck.id}: {truck.model}, rated {truck.rated_capacity}t, {truck.fuel_type}")
    print(f"{shovel.id}: {shovel.model}, rated {shovel.rated_capacity}t")

    print()
    print("--- 2. Shared behaviour lives on the base; specifics live on the leaf ---")
    print(
        f"operational states (identical for both): {[s.value for s in RigidHaulTruck.operational_states]}"
    )
    assert RigidHaulTruck.operational_states == HydraulicShovel.operational_states
    assert OperationalState.OPERATING in RigidHaulTruck.operational_states
    print("(a truck and a shovel share one state machine -- that is why fleet-wide")
    print(" utilisation is even a meaningful question)")

    print()
    print("--- 3. Metadata declares which KPIs a type can support ---")
    print(f"RigidHaulTruck supports : {truck.meta.supported_kpis}")
    print(f"HydraulicShovel supports: {shovel.meta.supported_kpis}")

    print()
    print("--- 4. Location and organisation are modelled, not implied ---")
    mine = Mine(id="bingham-west", commodity_codes=("copper",), method="open_pit")
    pit = Pit(id="pit-west", mine_id=mine.id, commodity="copper")
    bench = Bench(id="bench-7", pit_id=pit.id, elevation_m=1820.0)
    fleet = Fleet(id="FL-NORTH", mine_id=mine.id, equipment_type_code=RigidHaulTruck.code)
    print(f"{mine.id} ({mine.method}) -> {pit.id} -> {bench.id} @ {bench.elevation_m}m")
    print(f"fleet {fleet.id} groups equipment_type_code={fleet.equipment_type_code!r}")

    print()
    print("--- 5. Relationships are explicit, typed edges between ids ---")
    edges = [
        Relationship(source_id=pit.id, kind=RelationshipKind.BELONGS_TO, target_id=mine.id),
        Relationship(source_id=bench.id, kind=RelationshipKind.BELONGS_TO, target_id=pit.id),
        Relationship(source_id=truck.id, kind=RelationshipKind.BELONGS_TO, target_id=fleet.id),
    ]
    for edge in edges:
        print(f"  {edge.source_id} --{edge.kind.value}--> {edge.target_id}")
    print("(edges, not nested objects: a Bench does not hold a pointer to its Pit,")
    print(" so each entity stays independently serializable -- design spec AD-ON-02)")

    print()
    print("--- 6. Production time is a modelled interval, not a naive timestamp ---")
    shift = Shift(
        id="A-2026-06-25",
        mine_id=mine.id,
        pattern="2x12",
        start_utc=datetime(2026, 6, 25, 6, tzinfo=timezone.utc),
        end_utc=datetime(2026, 6, 25, 18, tzinfo=timezone.utc),
        scheduled_h=12.0,
    )
    probe = datetime(2026, 6, 25, 14, 30, tzinfo=timezone.utc)
    print(
        f"shift {shift.id} ({shift.scheduled_h}h) contains {probe.isoformat()}: {shift.contains(probe)}"
    )

    print()
    print("--- 7. Every type exports its shape as JSON Schema ---")
    schema = truck.to_schema()
    print(json.dumps({k: schema[k] for k in list(schema)[:3]}, indent=2))
    print("(dashboards, agents, and integrations read this instead of guessing)")


if __name__ == "__main__":
    main()
