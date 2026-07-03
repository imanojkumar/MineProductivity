"""Model equipment: declare leaf types, inspect their metadata, and
export their shape as JSON Schema.

Mirrors Developer & Cookbook Guide Part I, Chapter 8's worked example of
the equipment inheritance split: common behaviour (the operational state
machine, rated capacity) lives on `EquipmentType`; specifics (fuel type,
throughput) live on the leaves.

Run: python examples/ontology/01_equipment_modelling.py
"""

from __future__ import annotations

import json

from mineproductivity.ontology import (
    Fleet,
    HydraulicShovel,
    OperationalState,
    RigidHaulTruck,
)


def main() -> None:
    print("--- Construct a RigidHaulTruck ---")
    truck = RigidHaulTruck(
        id="HT-214",
        model="CAT 797F",
        fuel_type="diesel",
        fleet_id="FL-NORTH",
        rated_capacity=363.0,
    )
    print(f"id={truck.id} model={truck.model} rated_capacity={truck.rated_capacity}t")

    print()
    print("--- Construct a HydraulicShovel loading that same fleet's trucks ---")
    shovel = HydraulicShovel(id="SH-1", model="EX8000", fleet_id="FL-NORTH", rated_capacity=42.0)
    print(f"id={shovel.id} model={shovel.model} rated_capacity={shovel.rated_capacity}t")

    print()
    print("--- Every leaf type shares the same four-state operational state machine ---")
    print(
        f"RigidHaulTruck.operational_states: {[s.value for s in RigidHaulTruck.operational_states]}"
    )
    assert RigidHaulTruck.operational_states == HydraulicShovel.operational_states
    assert OperationalState.OPERATING in RigidHaulTruck.operational_states

    print()
    print("--- Declared metadata drives which KPIs a leaf type supports ---")
    print(f"RigidHaulTruck.meta.supported_kpis: {truck.meta.supported_kpis}")
    print(f"HydraulicShovel.meta.supported_kpis: {shovel.meta.supported_kpis}")

    print()
    print("--- A Fleet groups equipment of one type, by equipment_type_code ---")
    fleet = Fleet(id="FL-NORTH", mine_id="bingham-west", equipment_type_code=RigidHaulTruck.code)
    print(f"fleet {fleet.id} groups equipment_type_code={fleet.equipment_type_code!r}")

    print()
    print("--- Export a leaf type's shape as JSON Schema (dashboards/AI agents read this) ---")
    schema = truck.to_schema()
    print(json.dumps(schema, indent=2))


if __name__ == "__main__":
    main()
