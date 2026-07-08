"""``by_category``/``by_scope`` composed lookups over a populated
``TwinRepository`` -- twin discovery is plain
``core.BaseSpecification`` composition over
``core.BaseRepository.list()``, no bespoke query mechanism (design spec
§18).

Run: python examples/digital_twin/02_discovery.py
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import ClassVar

from mineproductivity.core import InMemoryRepository
from mineproductivity.digital_twin import (
    ConveyorTwin,
    StockpileTwin,
    Twin,
    TwinCategory,
    TwinContext,
    TwinMetadata,
    TwinState,
    by_category,
    by_scope,
)
from mineproductivity.events import BaseEvent

MOMENT = datetime(2026, 7, 8, 6, 0, tzinfo=timezone.utc)


class BeltConveyorTwin(ConveyorTwin):
    """A belt conveyor twin (discovery demo)."""

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="CONVEYOR.DiscoveryBelt",
        category=TwinCategory.CONVEYOR,
        description="A belt conveyor twin (discovery demo).",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        return self.state


class OreStockpileTwin(StockpileTwin):
    """An ore stockpile twin (discovery demo)."""

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="STOCKPILE.DiscoveryOre",
        category=TwinCategory.STOCKPILE,
        description="An ore stockpile twin (discovery demo).",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        return self.state


def _state(**attributes: float) -> TwinState:
    return TwinState(attributes=dict(attributes), captured_at=MOMENT)


def main() -> None:
    print("--- 1. A repository holding twins across categories and pits ---")
    repository: InMemoryRepository[Twin, str] = InMemoryRepository()
    repository.add(
        BeltConveyorTwin(
            id="CONV-7",
            scope={"equipment_id": "CONV-7", "pit": "north"},
            state=_state(belt_speed_mps=3.1),
        )
    )
    repository.add(
        BeltConveyorTwin(
            id="CONV-8",
            scope={"equipment_id": "CONV-8", "pit": "south"},
            state=_state(belt_speed_mps=2.9),
        )
    )
    repository.add(
        OreStockpileTwin(
            id="SP-1",
            scope={"stockpile_id": "SP-1", "pit": "north"},
            state=_state(volume_t=18_500.0),
        )
    )
    print(f"{len(repository.list())} twins provisioned")

    print()
    print("--- 2. by_category: which twin instances are conveyors? ---")
    conveyors = repository.list(by_category(TwinCategory.CONVEYOR))
    print(f"conveyors: {sorted(twin.id for twin in conveyors)}")

    print()
    print("--- 3. by_scope: everything in the north pit ---")
    north = repository.list(by_scope({"pit": "north"}))
    print(f"north pit: {sorted(twin.id for twin in north)}")

    print()
    print("--- 4. Composition with the core &/|/~ operators ---")
    north_conveyors = repository.list(
        by_category(TwinCategory.CONVEYOR) & by_scope({"pit": "north"})
    )
    print(f"north-pit conveyors: {[twin.id for twin in north_conveyors]}")
    non_conveyors = repository.list(~by_category(TwinCategory.CONVEYOR))
    print(f"everything else: {[twin.id for twin in non_conveyors]}")

    print()
    print("--- 5. A filter matching nothing returns an empty sequence, never raises ---")
    print(f"ventilation twins: {list(repository.list(by_category(TwinCategory.VENTILATION)))}")


if __name__ == "__main__":
    main()
