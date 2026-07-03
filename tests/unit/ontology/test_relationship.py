"""Tests for mineproductivity.ontology.relationship."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.ontology.exceptions import RelationshipError
from mineproductivity.ontology.relationship import Relationship, RelationshipKind


class TestRelationshipKind:
    def test_has_five_kinds(self) -> None:
        assert len(list(RelationshipKind)) == 5

    def test_values(self) -> None:
        assert RelationshipKind.BELONGS_TO.value == "belongs_to"
        assert RelationshipKind.PART_OF.value == "part_of"
        assert RelationshipKind.OPERATED_BY.value == "operated_by"
        assert RelationshipKind.LOCATED_AT.value == "located_at"
        assert RelationshipKind.SCOPED_TO.value == "scoped_to"


class TestConstruction:
    def test_valid_construction(self) -> None:
        rel = Relationship(
            source_id="bench-7", kind=RelationshipKind.BELONGS_TO, target_id="pit-west"
        )
        assert rel.source_id == "bench-7"
        assert rel.target_id == "pit-west"
        assert rel.kind is RelationshipKind.BELONGS_TO

    def test_is_frozen(self) -> None:
        rel = Relationship(source_id="a", kind=RelationshipKind.PART_OF, target_id="b")
        with pytest.raises(dataclasses.FrozenInstanceError):
            rel.source_id = "c"  # type: ignore[misc]


class TestValidation:
    def test_empty_source_id_rejected(self) -> None:
        with pytest.raises(RelationshipError):
            Relationship(source_id="", kind=RelationshipKind.BELONGS_TO, target_id="b")

    def test_whitespace_only_source_id_rejected(self) -> None:
        with pytest.raises(RelationshipError):
            Relationship(source_id="   ", kind=RelationshipKind.BELONGS_TO, target_id="b")

    def test_empty_target_id_rejected(self) -> None:
        with pytest.raises(RelationshipError):
            Relationship(source_id="a", kind=RelationshipKind.BELONGS_TO, target_id="")


class TestStructuralEquality:
    def test_equal_when_fields_match(self) -> None:
        a = Relationship(source_id="a", kind=RelationshipKind.BELONGS_TO, target_id="b")
        b = Relationship(source_id="a", kind=RelationshipKind.BELONGS_TO, target_id="b")
        assert a == b

    def test_not_equal_when_kind_differs(self) -> None:
        a = Relationship(source_id="a", kind=RelationshipKind.BELONGS_TO, target_id="b")
        b = Relationship(source_id="a", kind=RelationshipKind.PART_OF, target_id="b")
        assert a != b
