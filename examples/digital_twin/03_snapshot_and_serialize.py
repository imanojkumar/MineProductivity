"""``TwinSnapshot`` capture and a ``core.serialization`` round-trip --
a snapshot pairs one twin's derived state with the ``events.AsOf`` it
was captured at, and every value type in this package serializes
generically, with no bespoke per-type serializer (design spec §13,
§19).

Run: python examples/digital_twin/03_snapshot_and_serialize.py
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import ClassVar

from mineproductivity.core.serialization import to_dict
from mineproductivity.digital_twin import (
    StockpileTwin,
    TwinCategory,
    TwinContext,
    TwinMetadata,
    TwinSnapshot,
    TwinState,
    TwinStatus,
)
from mineproductivity.events import AsOf, BaseEvent

MOMENT = datetime(2026, 7, 8, 6, 0, tzinfo=timezone.utc)


class OreStockpileTwin(StockpileTwin):
    """An ore stockpile's live volume/grade state (snapshot demo)."""

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="STOCKPILE.Ore",
        category=TwinCategory.STOCKPILE,
        description="An ore stockpile twin tracking volume and grade.",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        return self.state


def main() -> None:
    print("--- 1. A synchronized stockpile twin ---")
    twin = OreStockpileTwin(
        id="SP-1",
        scope={"stockpile_id": "SP-1", "pit": "north"},
        state=TwinState(
            attributes={"volume_t": 18_500.0, "grade_gpt": 1.42},
            captured_at=MOMENT,
        ),
        status=TwinStatus.SYNCHRONIZED,
    )
    print(f"{twin.id}: {dict(twin.state.attributes)}")

    print()
    print("--- 2. Capture a point-in-time snapshot (reusing events.AsOf) ---")
    snapshot = TwinSnapshot(
        twin_id=twin.id,
        state=twin.state,
        status=twin.status,
        as_of=AsOf(utc=MOMENT + timedelta(hours=2)),
    )
    print(f"snapshot of {snapshot.twin_id} as of {snapshot.as_of.utc}")

    print()
    print("--- 3. Serialize via core.serialization -- generically, no bespoke serializer ---")
    data = to_dict(snapshot)
    print(f"twin_id:        {data['twin_id']}")
    print(f"state:          {data['state']['attributes']}")
    print(f"schema_version: {data['state']['schema_version']}")

    print()
    print("--- 4. Round trip: the rebuilt snapshot reproduces state/status/as_of exactly ---")
    rebuilt = TwinSnapshot(
        twin_id=data["twin_id"],
        state=TwinState(**data["state"]),
        status=data["status"],
        as_of=AsOf(**data["as_of"]),
    )
    print(f"rebuilt == original: {rebuilt == snapshot}")
    print(f"state equal:         {rebuilt.state == snapshot.state}")
    print(f"status preserved:    {rebuilt.status is snapshot.status}")

    print()
    print("--- 5. A snapshot can seed a hypothetical fork (scenario AsOf) ---")
    fork_reference = AsOf(scenario="what-if-reclaim-rate-doubles")
    fork = TwinSnapshot(twin_id=twin.id, state=twin.state, status=twin.status, as_of=fork_reference)
    print(
        f"forked snapshot carries scenario={fork.as_of.scenario!r} -- the hook a future"
        " TwinSimulationModel implementer consumes"
    )


if __name__ == "__main__":
    main()
