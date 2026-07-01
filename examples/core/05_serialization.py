"""BaseSerializer + DataclassSerializer + to_dict: converting between
in-memory objects and plain, JSON-safe mappings.

Run: python examples/core/05_serialization.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from mineproductivity.core import BaseValueObject, DataclassSerializer, to_dict


@dataclass(frozen=True, slots=True)
class Reading(BaseValueObject):
    sensor_id: str
    value: float
    unit: str


def main() -> None:
    reading = Reading(sensor_id="S-1", value=42.5, unit="celsius")

    print("--- DataclassSerializer ---")
    serializer = DataclassSerializer(Reading)
    payload = serializer.serialize(reading)
    print(f"serialize(reading) -> {payload}")
    print(f"as JSON -> {json.dumps(payload)}")

    restored = serializer.deserialize(payload)
    print(f"deserialize(payload) -> {restored}")
    print(f"restored == reading: {restored == reading}")

    print()
    print("--- to_dict() convenience helper ---")
    print(f"to_dict(reading) -> {to_dict(reading)}")

    class WithCustomToDict:
        def to_dict(self) -> dict[str, str]:
            return {"custom": "shape"}

    print(f"to_dict(object with its own to_dict()) -> {to_dict(WithCustomToDict())}")


if __name__ == "__main__":
    main()
