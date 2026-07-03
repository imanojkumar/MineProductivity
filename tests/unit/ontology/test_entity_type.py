"""Tests for mineproductivity.ontology.entity_type."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from enum import Enum
from typing import ClassVar, Literal

import pytest

from mineproductivity.core import DuplicateError, Maybe
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    _EntityTypeRegistry,
    _json_type_for,
    get_entity_type,
    lookup_entity_type,
    register_entity_type,
    registered_entity_type_codes,
)
from mineproductivity.ontology.exceptions import OntologyValidationError, UnknownEntityTypeError


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class _Widget(BaseEntityType):
    code: ClassVar[str] = "TEST_WIDGET"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Widget",
        description="A test-only entity type.",
        supported_kpis=("TEST.Rate",),
    )

    size: float
    label: str = dataclasses.field(default="", kw_only=True)

    def validate(self) -> None:
        if self.size < 0:
            raise OntologyValidationError("_Widget.size must be >= 0")


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class _NormalizingWidget(BaseEntityType):
    code: ClassVar[str] = "TEST_NORMALIZING_WIDGET"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(name="N", description="d")

    label: str

    def _normalize(self) -> None:
        object.__setattr__(self, "label", self.label.strip().upper())


class TestEntityTypeMetadata:
    def test_defaults(self) -> None:
        meta = EntityTypeMetadata(name="X", description="d")
        assert meta.supported_kpis == ()
        assert meta.parent_code is None

    def test_declares_supported_kpis_and_parent_code(self) -> None:
        meta = EntityTypeMetadata(name="X", description="d", supported_kpis=("A",), parent_code="Y")
        assert meta.supported_kpis == ("A",)
        assert meta.parent_code == "Y"


class TestConstructionAndValidation:
    def test_valid_construction(self) -> None:
        widget = _Widget(id="w-1", size=3.0)
        assert widget.size == 3.0

    def test_validate_rejects_negative_size(self) -> None:
        with pytest.raises(OntologyValidationError):
            _Widget(id="w-2", size=-1.0)

    def test_normalize_runs_before_validate(self) -> None:
        widget = _NormalizingWidget(id="n-1", label="  hello  ")
        assert widget.label == "HELLO"

    def test_is_frozen(self) -> None:
        widget = _Widget(id="w-3", size=1.0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            widget.size = 2.0  # type: ignore[misc]


class TestIdentityEquality:
    def test_same_id_equal_despite_different_fields(self) -> None:
        a = _Widget(id="same", size=1.0)
        b = _Widget(id="same", size=999.0)
        assert a == b

    def test_different_id_not_equal(self) -> None:
        a = _Widget(id="a", size=1.0)
        b = _Widget(id="b", size=1.0)
        assert a != b

    def test_hashable_by_id(self) -> None:
        a = _Widget(id="same", size=1.0)
        b = _Widget(id="same", size=2.0)
        assert hash(a) == hash(b)
        assert len({a, b}) == 1


class TestToSchema:
    def test_schema_contains_expected_shape(self) -> None:
        schema = _Widget(id="w-4", size=1.0).to_schema()
        assert schema["title"] == "TEST_WIDGET"
        assert schema["type"] == "object"
        assert "id" not in schema["properties"]
        assert schema["properties"]["size"] == {"type": "number"}
        assert schema["properties"]["label"] == {"type": "string"}

    def test_required_excludes_defaulted_fields(self) -> None:
        schema = _Widget(id="w-5", size=1.0).to_schema()
        assert "size" in schema["required"]
        assert "label" not in schema["required"]

    def test_schema_is_cached_per_type(self) -> None:
        first = _Widget(id="w-6", size=1.0).to_schema()
        second = _Widget(id="w-7", size=2.0).to_schema()
        assert first is second


class TestEntityTypeRegistry:
    def test_register_entity_type_returns_class_unchanged(self) -> None:
        assert register_entity_type(_Widget) is _Widget

    def test_registered_type_is_in_registered_codes(self) -> None:
        assert "TEST_WIDGET" in registered_entity_type_codes()

    def test_lookup_entity_type_found(self) -> None:
        found = lookup_entity_type("TEST_WIDGET")
        assert found == Maybe.some(_Widget)

    def test_lookup_entity_type_missing_returns_nothing(self) -> None:
        assert lookup_entity_type("DOES_NOT_EXIST").is_nothing

    def test_get_entity_type_found(self) -> None:
        assert get_entity_type("TEST_WIDGET") is _Widget

    def test_get_entity_type_missing_raises(self) -> None:
        with pytest.raises(UnknownEntityTypeError):
            get_entity_type("DOES_NOT_EXIST")

    def test_reregistering_same_class_is_idempotent(self) -> None:
        register_entity_type(_Widget)
        register_entity_type(_Widget)
        assert registered_entity_type_codes().count("TEST_WIDGET") == 1

    def test_registering_different_class_under_same_code_raises_duplicate_error(self) -> None:
        @dataclasses.dataclass(frozen=True, slots=True, eq=False)
        class _Impostor(BaseEntityType):
            code: ClassVar[str] = "TEST_WIDGET"
            meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
                name="Impostor", description="d"
            )

        with pytest.raises(DuplicateError):
            register_entity_type(_Impostor)


class _Colour(Enum):
    RED = "red"


class TestJsonTypeFor:
    def test_none_type_maps_to_string(self) -> None:
        assert _json_type_for(None) == "string"

    def test_optional_str_unwraps_to_string(self) -> None:
        assert _json_type_for(str | None) == "string"

    def test_optional_float_unwraps_to_number(self) -> None:
        assert _json_type_for(float | None) == "number"

    def test_enum_maps_to_string(self) -> None:
        assert _json_type_for(_Colour) == "string"

    def test_tuple_maps_to_array(self) -> None:
        assert _json_type_for(tuple[str, ...]) == "array"

    def test_dict_maps_to_object(self) -> None:
        assert _json_type_for(dict[str, float]) == "object"

    def test_mapping_maps_to_object(self) -> None:
        assert _json_type_for(Mapping[str, float]) == "object"

    def test_plain_str_maps_to_string(self) -> None:
        assert _json_type_for(str) == "string"

    def test_plain_float_maps_to_number(self) -> None:
        assert _json_type_for(float) == "number"

    def test_plain_int_maps_to_integer(self) -> None:
        assert _json_type_for(int) == "integer"

    def test_plain_bool_maps_to_boolean(self) -> None:
        assert _json_type_for(bool) == "boolean"

    def test_unrecognized_non_type_falls_back_to_string(self) -> None:
        assert _json_type_for(Literal["open_pit", "underground"]) == "string"


class TestEntityTypeRegistryContainerProtocol:
    def test_len_reflects_registration_count(self) -> None:
        registry = _EntityTypeRegistry()
        assert len(registry) == 0
        registry.register(_Widget)
        assert len(registry) == 1

    def test_contains_reflects_registration(self) -> None:
        registry = _EntityTypeRegistry()
        assert "TEST_WIDGET" not in registry
        registry.register(_Widget)
        assert "TEST_WIDGET" in registry
