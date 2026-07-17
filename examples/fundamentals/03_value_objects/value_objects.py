"""Lesson 03 -- Value objects: measurements that are defined by what they are.

A grade of 0.62% Cu is not "a particular" grade with an identity -- any
0.62% Cu is interchangeable with any other. The same is true of a
payload, a cycle time, or a set of pit coordinates. Those are *value
objects*: frozen, compared by their fields, self-validating, and
replaced rather than mutated.

Modelling a measurement as a value object is how the platform stops
unit-less floats from leaking through the system: an ``OreGrade`` cannot
be negative, and a ``Payload`` cannot exceed the truck's rated capacity,
because the object refuses to exist in that state.

Run: python examples/fundamentals/03_value_objects/value_objects.py
"""

from __future__ import annotations

from dataclasses import dataclass

from mineproductivity.core import BaseValueObject, ValidationError


@dataclass(frozen=True, slots=True)
class OreGrade(BaseValueObject):
    """Copper grade of a parcel of ore, as a percentage by mass."""

    percent_cu: float

    def validate(self) -> None:
        if not (0.0 <= self.percent_cu <= 100.0):
            raise ValidationError(f"percent_cu must be within 0-100, got {self.percent_cu}")


@dataclass(frozen=True, slots=True)
class Payload(BaseValueObject):
    """Tonnes carried in one truck load, against the truck's rated capacity."""

    tonnes: float
    rated_capacity_t: float

    def validate(self) -> None:
        if self.tonnes < 0:
            raise ValidationError(f"tonnes must not be negative, got {self.tonnes}")
        if self.tonnes > self.rated_capacity_t:
            raise ValidationError(
                f"payload {self.tonnes}t exceeds rated capacity {self.rated_capacity_t}t"
            )

    @property
    def utilisation(self) -> float:
        """Fraction of the truck's rated capacity actually used."""
        return self.tonnes / self.rated_capacity_t


def main() -> None:
    print("--- 1. Equality is by value: two 0.62% grades are the same grade ---")
    face_sample = OreGrade(percent_cu=0.62)
    lab_sample = OreGrade(percent_cu=0.62)
    print(f"face_sample == lab_sample -> {face_sample == lab_sample}")
    print(f"hash equal -> {hash(face_sample) == hash(lab_sample)}")
    print("(no identity: a grade is not 'a particular' grade, it IS its value)")

    print()
    print("--- 2. Self-validating: an impossible measurement cannot be constructed ---")
    try:
        OreGrade(percent_cu=-4.0)
    except ValidationError as exc:
        print(f"rejected: {exc}")

    print()
    print("--- 3. Domain rules live on the object, not in the caller ---")
    # A CAT 793F's nominal payload is ~226 t; a well-loaded truck sits near it.
    load = Payload(tonnes=220.0, rated_capacity_t=226.0)
    print(f"payload {load.tonnes}t on a {load.rated_capacity_t}t truck")
    print(f"capacity utilisation: {load.utilisation:.1%}")
    try:
        Payload(tonnes=245.0, rated_capacity_t=226.0)
    except ValidationError as exc:
        print(f"overload rejected: {exc}")

    print()
    print("--- 4. Change means replace: the original value is never mutated ---")
    reassayed = face_sample.replace(percent_cu=0.58)
    print(f"face_sample.replace(percent_cu=0.58) -> {reassayed.percent_cu}% Cu")
    print(f"original still: {face_sample.percent_cu}% Cu")
    print("(replace() re-runs validate(), so the new value is legal too)")

    print()
    print("--- 5. Values compose into richer values, still validated end to end ---")
    loads = [
        Payload(tonnes=218.0, rated_capacity_t=226.0),
        Payload(tonnes=225.0, rated_capacity_t=226.0),
        Payload(tonnes=210.0, rated_capacity_t=226.0),
    ]
    total = sum(load.tonnes for load in loads)
    mean_util = sum(load.utilisation for load in loads) / len(loads)
    print(f"3 loads moved {total:.0f}t at {mean_util:.1%} mean capacity utilisation")
    print("(every tonne in that total came from an object that proved itself valid)")


if __name__ == "__main__":
    main()
