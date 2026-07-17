"""Lesson 02 -- Entities: things with an identity that outlives their state.

A haul truck is still the same truck after it is refuelled, relocated,
reassigned to another fleet, or rebuilt. Its *identity* (HT-214) is
stable; its *state* is not. That is exactly what ``core.BaseEntity``
models: equality and hashing come from ``id`` alone, and every state
change produces a new, immutable instance.

Run: python examples/fundamentals/02_entities/entities.py
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from mineproductivity.core import BaseEntity, InMemoryRepository


# eq=False is required on every BaseEntity subclass: dataclasses would
# otherwise generate a field-based __eq__ that silently replaces the
# identity-based one BaseEntity defines. See Common mistakes in the tutorial.
@dataclass(frozen=True, slots=True, eq=False)
class HaulTruck(BaseEntity[str]):
    """One physical haul truck, identified by its fleet number."""

    model: str
    fleet_id: str
    odometer_km: float
    operational_state: str


def main() -> None:
    print("--- 1. Identity is the truck's fleet number, not its condition ---")
    truck = HaulTruck(
        id="HT-214",
        model="CAT 793F",
        fleet_id="FL-NORTH",
        odometer_km=412_880.0,
        operational_state="operating",
    )
    print(f"{truck.id}: {truck.model} in {truck.fleet_id} @ {truck.odometer_km:,.0f} km")

    print()
    print("--- 2. The truck hauls a shift: new odometer, new state, same truck ---")
    after_shift = dataclasses.replace(
        truck,
        odometer_km=truck.odometer_km + 318.0,
        operational_state="standby",
    )
    print(f"before: {truck.odometer_km:,.0f} km, {truck.operational_state}")
    print(f"after : {after_shift.odometer_km:,.0f} km, {after_shift.operational_state}")
    print(f"same truck? truck == after_shift -> {truck == after_shift}")
    print("(identity-based equality: HT-214 is HT-214 regardless of odometer)")

    print()
    print("--- 3. A different truck with identical specs is NOT the same truck ---")
    spare = dataclasses.replace(truck, id="HT-215")
    print(f"truck == spare -> {truck == spare}  (HT-214 vs HT-215)")
    print(f"hash(truck) == hash(after_shift) -> {hash(truck) == hash(after_shift)}")
    print("(hashing by id is what lets a truck be a dict key across state changes)")

    print()
    print("--- 4. Immutability: the original instance is never mutated ---")
    try:
        truck.odometer_km = 0.0  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        print("assignment rejected: entities are frozen; change means a NEW instance")

    print()
    print("--- 5. A repository stores instances, keyed by identity ---")
    fleet: InMemoryRepository[HaulTruck, str] = InMemoryRepository()
    fleet.add(truck)
    fleet.add(spare)
    print(f"fleet holds {len(fleet.list())} trucks: {sorted(t.id for t in fleet.list())}")

    # Recording the post-shift state = replacing the instance under the same id.
    fleet.remove("HT-214")
    fleet.add(after_shift)
    print(f"HT-214 odometer now: {fleet.get('HT-214').odometer_km:,.0f} km")
    print("(the repository is keyed by id -- the truck never became a different truck)")


if __name__ == "__main__":
    main()
