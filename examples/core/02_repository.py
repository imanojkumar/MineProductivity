"""BaseRepository + BaseSpecification: storing and querying entities.

Run: python examples/core/02_repository.py
"""

from __future__ import annotations

from dataclasses import dataclass

from mineproductivity.core import (
    BaseEntity,
    BaseSpecification,
    DuplicateError,
    InMemoryRepository,
    NotFoundError,
)


@dataclass(frozen=True, slots=True, eq=False)
class Sensor(BaseEntity[str]):
    name: str
    battery_percent: int


class IsLowBattery(BaseSpecification[Sensor]):
    def is_satisfied_by(self, candidate: Sensor) -> bool:
        return candidate.battery_percent < 20


def main() -> None:
    repo: InMemoryRepository[Sensor, str] = InMemoryRepository()

    repo.add(Sensor(id="S-1", name="Vibration A", battery_percent=85))
    repo.add(Sensor(id="S-2", name="Vibration B", battery_percent=12))
    repo.add(Sensor(id="S-3", name="Temperature C", battery_percent=8))

    print(f"total sensors: {len(repo.list())}")

    low_battery = repo.list(IsLowBattery())
    print(f"low battery sensors: {[s.name for s in low_battery]}")

    found = repo.find("S-1")
    print(f"find('S-1').is_some: {found.is_some}, name: {found.unwrap().name}")

    missing = repo.find("does-not-exist")
    name_or_default = missing.map(lambda sensor: sensor.name).unwrap_or("<not found>")
    print(f"find('does-not-exist') name-or-default: {name_or_default}")

    try:
        repo.add(Sensor(id="S-1", name="duplicate", battery_percent=50))
    except DuplicateError as exc:
        print(f"adding a duplicate id raised: {exc}")

    try:
        repo.get("does-not-exist")
    except NotFoundError as exc:
        print(f"getting a missing id raised: {exc}")

    repo.remove("S-3")
    print(f"after remove('S-3'): {[s.id for s in repo.list()]}")


if __name__ == "__main__":
    main()
