"""Entity vs. Value Object: the two ways to define equality in the domain model.

Run: python examples/core/01_entity_and_value_object.py
"""

from __future__ import annotations

from dataclasses import dataclass

from mineproductivity.core import BaseEntity, BaseValueObject


# A value object: equality is defined entirely by its fields.
@dataclass(frozen=True, slots=True)
class Coordinates(BaseValueObject):
    latitude: float
    longitude: float

    def validate(self) -> None:
        if not (-90 <= self.latitude <= 90):
            raise ValueError("latitude must be between -90 and 90")


# An entity: equality is defined entirely by its id, regardless of fields.
@dataclass(frozen=True, slots=True, eq=False)
class Asset(BaseEntity[str]):
    name: str
    location: Coordinates


def main() -> None:
    print("--- BaseValueObject: equality by value ---")
    a = Coordinates(latitude=40.7128, longitude=-74.0060)
    b = Coordinates(latitude=40.7128, longitude=-74.0060)
    print(f"a == b: {a == b}  (same coordinates, different instances)")
    print(f"hash(a) == hash(b): {hash(a) == hash(b)}")

    moved = a.replace(longitude=-73.9)
    print(f"a.replace(longitude=-73.9) -> {moved}")
    print(f"original a unchanged: {a}")

    try:
        Coordinates(latitude=999, longitude=0)
    except ValueError as exc:
        print(f"invalid coordinates rejected: {exc}")

    print()
    print("--- BaseEntity: equality by identity ---")
    original = Asset(id="A-1", name="Crusher #1", location=a)
    relocated = Asset(id="A-1", name="Crusher #1", location=moved)
    different_asset = Asset(id="A-2", name="Crusher #1", location=a)

    print(f"original == relocated: {original == relocated}  (same id, different location)")
    print(f"original == different_asset: {original == different_asset}  (different id)")
    print(f"repr(original): {original!r}")


if __name__ == "__main__":
    main()
