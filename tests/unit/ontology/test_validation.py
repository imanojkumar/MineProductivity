"""Tests for mineproductivity.ontology.validation."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)
from mineproductivity.ontology.validation import OntologyValidator


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class _Gadget(BaseEntityType):
    code: ClassVar[str] = "TEST_GADGET"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(name="Gadget", description="d")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class _Assembly(BaseEntityType):
    code: ClassVar[str] = "TEST_ASSEMBLY"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(name="Assembly", description="d")

    gadget_type_code: str
    site_id: str = dataclasses.field(default="", kw_only=True)


class TestSelfContainedTypeCodeResolution:
    def test_known_type_code_is_valid(self) -> None:
        validator = OntologyValidator()
        assembly = _Assembly(id="a-1", gadget_type_code="TEST_GADGET")
        result = validator.validate(assembly)
        assert result.is_valid
        assert result.errors == ()

    def test_unknown_type_code_produces_error(self) -> None:
        validator = OntologyValidator()
        assembly = _Assembly(id="a-2", gadget_type_code="NOT_A_TYPE")
        result = validator.validate(assembly)
        assert not result.is_valid
        assert "NOT_A_TYPE" in result.errors[0]

    def test_empty_type_code_field_is_skipped(self) -> None:
        validator = OntologyValidator()
        assembly = _Assembly(id="a-3", gadget_type_code="TEST_GADGET", site_id="")
        result = validator.validate(assembly)
        assert result.is_valid


class TestInjectedIdResolver:
    def test_no_resolver_skips_id_fields(self) -> None:
        validator = OntologyValidator()
        assembly = _Assembly(id="a-4", gadget_type_code="TEST_GADGET", site_id="unknown-site")
        result = validator.validate(assembly)
        assert result.is_valid

    def test_resolver_accepts_known_id(self) -> None:
        validator = OntologyValidator(entity_resolver=lambda eid: eid in {"site-1"})
        assembly = _Assembly(id="a-5", gadget_type_code="TEST_GADGET", site_id="site-1")
        result = validator.validate(assembly)
        assert result.is_valid

    def test_resolver_rejects_unknown_id(self) -> None:
        validator = OntologyValidator(entity_resolver=lambda eid: eid in {"site-1"})
        assembly = _Assembly(id="a-6", gadget_type_code="TEST_GADGET", site_id="unknown-site")
        result = validator.validate(assembly)
        assert not result.is_valid
        assert "unknown-site" in result.errors[0]

    def test_errors_accumulate_across_fields(self) -> None:
        validator = OntologyValidator(entity_resolver=lambda eid: False)
        assembly = _Assembly(id="a-7", gadget_type_code="NOT_A_TYPE", site_id="also-unknown")
        result = validator.validate(assembly)
        assert len(result.errors) == 2


class TestCallable:
    def test_validator_is_callable(self) -> None:
        validator = OntologyValidator()
        assembly = _Assembly(id="a-8", gadget_type_code="TEST_GADGET")
        assert validator(assembly).is_valid
