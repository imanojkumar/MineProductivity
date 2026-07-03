"""The five-minute tour: one truck, one shift, one KPI.

The shortest path from "just installed MineProductivity" to "computed a
real number" -- model a truck (`ontology`), record two haul cycles
(`events`), and read the shift's throughput straight off the KPI
Standard Library (`kpis`). Each of the four packages this touches has
its own, deeper example next door:

- `examples/ontology/01_equipment_modelling.py` -- more equipment types,
  metadata, JSON Schema export.
- `examples/events/01_first_event.py` -- validation, envelopes, replay.
- `examples/kpis/01_simple_execution.py` -- the full `KPIEngine`, not
  just a direct `REGISTRY` lookup.
- `examples/connectors/01_csv_ingestion.py` -- where cycles like these
  actually come from in a real deployment.

Run: python examples/quickstart/01_five_minute_tour.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.kpis import REGISTRY
from mineproductivity.ontology import RigidHaulTruck, Shift


def main() -> None:
    print("--- 1. Model the truck (ontology) ---")
    truck = RigidHaulTruck(id="HT-214", model="CAT 797F", fuel_type="diesel", rated_capacity=363.0)
    print(f"{truck.id}: {truck.model}, rated {truck.rated_capacity} t")

    print()
    print("--- 2. Define the shift it worked (ontology) ---")
    shift = Shift(
        id="A-2026-06-25",
        mine_id="bingham-west",
        pattern="2x12",
        start_utc=datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc),
        end_utc=datetime(2026, 6, 25, 18, 0, tzinfo=timezone.utc),
        scheduled_h=12.0,
    )
    print(f"shift {shift.id}: {shift.scheduled_h}h scheduled")

    print()
    print("--- 3. Record two haul cycles it completed (a KPI-ready row shape) ---")
    cycles = [
        {"payload_t": 224.0, "operating_h": 0.35},
        {"payload_t": 218.0, "operating_h": 0.34},
    ]
    print(f"{len(cycles)} cycles, {sum(c['payload_t'] for c in cycles):.0f} t total")

    print()
    print("--- 4. Read PROD.TPH straight from the Standard Library (kpis) ---")
    tonnes_per_hour = REGISTRY.get("PROD.TPH")
    result = tonnes_per_hour().compute(cycles)
    print(f"{result.code} = {result.value:.1f} {result.unit}")

    print()
    print(f"That's it: {len(REGISTRY)} more KPIs are registered the same way -- see")
    print("`REGISTRY` and `examples/kpis/04_discovery.py` to explore them.")


if __name__ == "__main__":
    main()
