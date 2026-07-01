"""BaseFactory vs. BaseBuilder: two ways to encapsulate object construction.

Run: python examples/core/03_factory_and_builder.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from mineproductivity.core import BaseBuilder, BaseFactory, BaseValueObject


@dataclass(frozen=True, slots=True)
class Shift(BaseValueObject):
    crew: str
    start_hour: int
    duration_hours: int

    def validate(self) -> None:
        if not (0 <= self.start_hour < 24):
            raise ValueError("start_hour must be in [0, 24)")
        if self.duration_hours <= 0:
            raise ValueError("duration_hours must be positive")


# A factory: one-shot construction from keyword arguments.
class ShiftFactory(BaseFactory[Shift]):
    def create(self, **kwargs: Any) -> Shift:
        return Shift(
            crew=kwargs["crew"],
            start_hour=kwargs.get("start_hour", 6),
            duration_hours=kwargs.get("duration_hours", 8),
        )


# A builder: step-by-step fluent construction, useful for many optional steps.
class ShiftBuilder(BaseBuilder[Shift]):
    def __init__(self) -> None:
        self._crew = "unassigned"
        self._start_hour = 6
        self._duration_hours = 8

    def for_crew(self, crew: str) -> Self:
        self._crew = crew
        return self

    def starting_at(self, hour: int) -> Self:
        self._start_hour = hour
        return self

    def lasting(self, hours: int) -> Self:
        self._duration_hours = hours
        return self

    def build(self) -> Shift:
        return Shift(
            crew=self._crew,
            start_hour=self._start_hour,
            duration_hours=self._duration_hours,
        )


def main() -> None:
    print("--- BaseFactory ---")
    factory = ShiftFactory()
    shift = factory.create(crew="Alpha", start_hour=6, duration_hours=10)
    print(f"factory.create(...): {shift}")

    bad_result = factory.create_result(crew="Beta", start_hour=99)
    print(
        f"invalid input via create_result -> is_err: {bad_result.is_err}, error: {bad_result.error}"
    )

    print()
    print("--- BaseBuilder (fluent chaining) ---")
    night_shift = ShiftBuilder().for_crew("Night Crew").starting_at(18).lasting(12).build()
    print(f"builder chain -> {night_shift}")

    result = ShiftBuilder().for_crew("Bad").starting_at(30).build_result()
    print(f"invalid build via build_result -> is_err: {result.is_err}")


if __name__ == "__main__":
    main()
