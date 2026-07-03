"""Tests for mineproductivity.ontology.exceptions."""

from __future__ import annotations

import pytest

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.ontology.exceptions import (
    OntologyValidationError,
    RelationshipError,
    UnknownEntityTypeError,
)


class TestExceptionHierarchy:
    def test_ontology_validation_error_is_a_validation_error(self) -> None:
        assert issubclass(OntologyValidationError, ValidationError)

    def test_unknown_entity_type_error_is_a_not_found_error(self) -> None:
        assert issubclass(UnknownEntityTypeError, NotFoundError)

    def test_relationship_error_is_a_mineproductivity_error(self) -> None:
        assert issubclass(RelationshipError, MineProductivityError)

    @pytest.mark.parametrize(
        "exc_type",
        [OntologyValidationError, UnknownEntityTypeError, RelationshipError],
    )
    def test_catchable_as_root(self, exc_type: type[MineProductivityError]) -> None:
        with pytest.raises(MineProductivityError):
            raise exc_type("boom")

    @pytest.mark.parametrize(
        "exc_type",
        [OntologyValidationError, UnknownEntityTypeError, RelationshipError],
    )
    def test_carries_message(self, exc_type: type[MineProductivityError]) -> None:
        err = exc_type("boom")
        assert err.message == "boom"
