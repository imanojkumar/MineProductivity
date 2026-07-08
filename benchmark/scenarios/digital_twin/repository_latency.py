"""Benchmark scenario: ``TwinRepository.get()``/``list()`` latency at
representative twin-population scale (Digital Twin implementation
checklist, Benchmarks).

Standalone by design -- the ``mineproductivity.benchmark`` harness
package is not yet implemented (see ``benchmark/README.md``), so this
scenario is a plain script, mirroring
``benchmark/scenarios/decision/``'s established posture. Results are
recorded in ``benchmark/reports/digital_twin/``.

Scale rationale: one twin per asset -- a large site runs 10^2-10^3
twins (fleet + fixed plant); 10^3/10^4/10^5 spans "a large site"
through "an enterprise-wide, multi-site deployment, never pruned."
``get()`` is the hot per-sync path and must stay O(1) (design spec
§33); ``list()`` with a specification is the discovery path (§18),
linear by contract.

Run: python benchmark/scenarios/digital_twin/repository_latency.py
"""

from __future__ import annotations

import platform
import time
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import ClassVar

from mineproductivity.core import InMemoryRepository
from mineproductivity.digital_twin import (
    EquipmentTwin,
    Twin,
    TwinCategory,
    TwinContext,
    TwinMetadata,
    TwinState,
    by_scope,
)
from mineproductivity.events import BaseEvent

_EPOCH = datetime(2026, 7, 8, tzinfo=timezone.utc)

POPULATIONS = (1_000, 10_000, 100_000)
GET_REPEATS = 10_000
LIST_REPEATS = 5


class _BenchTwin(EquipmentTwin):
    """A minimal equipment twin for repository benchmarking."""

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="EQUIPMENT.Bench",
        category=TwinCategory.EQUIPMENT,
        description="A minimal equipment twin for repository benchmarking.",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        return self.state


def _twin(index: int) -> _BenchTwin:
    return _BenchTwin(
        id=f"EQ-{index:06d}",
        scope={"equipment_id": f"EQ-{index:06d}", "pit": "north" if index % 2 == 0 else "south"},
        state=TwinState(attributes={"operating": True}, captured_at=_EPOCH),
    )


def main() -> None:
    print("TwinRepository.get()/list() latency (core.InMemoryRepository reference)")
    print(f"python={platform.python_version()} machine={platform.machine()}")
    print()
    print(f"{'twins':>8} {'get_us':>8} {'list_all_ms':>12} {'list_scope_ms':>14} {'matches':>8}")

    for population in POPULATIONS:
        repository: InMemoryRepository[Twin, str] = InMemoryRepository()
        for index in range(population):
            repository.add(_twin(index))

        middle_id = f"EQ-{population // 2:06d}"
        start = time.perf_counter()
        for _ in range(GET_REPEATS):
            repository.get(middle_id)
        get_seconds = (time.perf_counter() - start) / GET_REPEATS

        start = time.perf_counter()
        for _ in range(LIST_REPEATS):
            everything = repository.list()
        list_all_seconds = (time.perf_counter() - start) / LIST_REPEATS

        specification = by_scope({"pit": "north"})
        start = time.perf_counter()
        for _ in range(LIST_REPEATS):
            matched = repository.list(specification)
        list_scope_seconds = (time.perf_counter() - start) / LIST_REPEATS

        assert len(everything) == population
        print(
            f"{population:>8} {get_seconds * 1e6:>8.2f} {list_all_seconds * 1e3:>12.2f}"
            f" {list_scope_seconds * 1e3:>14.2f} {len(matched):>8}"
        )


if __name__ == "__main__":
    main()
