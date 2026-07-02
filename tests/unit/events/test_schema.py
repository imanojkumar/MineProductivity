"""Tests for mineproductivity.events.schema."""

from __future__ import annotations

import pytest

from mineproductivity.events.exceptions import EventValidationError
from mineproductivity.events.schema import EventSchema
from mineproductivity.events.versioning import EventVersion


def make_schema(**overrides: object) -> EventSchema:
    defaults: dict[str, object] = dict(
        event_type_code="CYCLE",
        version=EventVersion(),
        required_fields=("payload_t",),
        field_types={"payload_t": "float"},
    )
    defaults.update(overrides)
    return EventSchema(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_minimal_construction(self) -> None:
        schema = make_schema()
        assert schema.event_type_code == "CYCLE"
        assert schema.invariants == ()

    def test_with_invariants(self) -> None:
        schema = make_schema(invariants=("payload_t >= 0",))
        assert schema.invariants == ("payload_t >= 0",)


class TestValidation:
    def test_lowercase_event_type_code_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_schema(event_type_code="cycle")

    def test_empty_event_type_code_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_schema(event_type_code="")

    def test_required_field_not_in_field_types_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_schema(
                required_fields=("payload_t", "missing_field"), field_types={"payload_t": "float"}
            )


class TestToJsonSchema:
    def test_required_fields_present(self) -> None:
        schema = make_schema()
        assert schema.to_json_schema()["required"] == ["payload_t"]

    def test_property_types_mapped(self) -> None:
        schema = make_schema(field_types={"payload_t": "float", "note": "unknown_type"})
        properties = schema.to_json_schema()["properties"]
        assert properties["payload_t"]["type"] == "number"
        assert properties["note"]["type"] == "string"  # unknown types default to string

    def test_title_is_event_type_code(self) -> None:
        assert make_schema().to_json_schema()["title"] == "CYCLE"
