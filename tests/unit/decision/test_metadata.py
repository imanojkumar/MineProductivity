"""Tests for mineproductivity.decision.metadata."""

from __future__ import annotations

import pytest

from mineproductivity.core import ValidationError

from mineproductivity.decision.exceptions import DecisionValidationError
from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "code": "STRATEGY.Threshold",
        "category": DecisionCategory.STRATEGY,
        "description": "Evaluate a Policy's rules against a DecisionContext.",
    }
    fields.update(overrides)
    return fields


class TestDecisionCategory:
    def test_members(self) -> None:
        assert {member.value for member in DecisionCategory} == {
            "strategy",
            "ranking",
            "root_cause",
            "what_if",
        }


class TestDecisionMetadataConstruction:
    def test_minimal_valid_construction(self) -> None:
        meta = DecisionMetadata(**_valid_kwargs())
        assert meta.code == "STRATEGY.Threshold"
        assert meta.category is DecisionCategory.STRATEGY
        assert meta.version == "1.0.0"

    def test_name_defaults_to_code_when_not_supplied(self) -> None:
        meta = DecisionMetadata(**_valid_kwargs())
        assert meta.name == meta.code

    def test_explicit_name_is_preserved(self) -> None:
        meta = DecisionMetadata(**_valid_kwargs(name="Threshold Strategy"))
        assert meta.name == "Threshold Strategy"

    def test_code_is_a_required_field_with_no_default(self) -> None:
        with pytest.raises(TypeError):
            DecisionMetadata(  # type: ignore[call-arg]
                category=DecisionCategory.STRATEGY, description="x"
            )

    def test_category_is_a_required_keyword_field(self) -> None:
        with pytest.raises(TypeError):
            DecisionMetadata(code="STRATEGY.Threshold", description="x")  # type: ignore[call-arg]

    def test_description_is_a_required_keyword_field(self) -> None:
        with pytest.raises(TypeError):
            DecisionMetadata(  # type: ignore[call-arg]
                code="STRATEGY.Threshold", category=DecisionCategory.STRATEGY
            )


class TestDecisionMetadataValidate:
    def test_valid_metadata_passes(self) -> None:
        DecisionMetadata(**_valid_kwargs())  # must not raise

    def test_empty_code_raises_decision_validation_error(self) -> None:
        with pytest.raises(DecisionValidationError, match="code must not be empty"):
            DecisionMetadata(**_valid_kwargs(code=""))

    def test_whitespace_only_code_raises(self) -> None:
        with pytest.raises(DecisionValidationError, match="code must not be empty"):
            DecisionMetadata(**_valid_kwargs(code="   "))


class TestDecisionMetadataReplace:
    def test_replace_reruns_normalize_and_validate(self) -> None:
        meta = DecisionMetadata(**_valid_kwargs())
        replaced = meta.replace(code="RANKING.Weighted")
        assert replaced.code == "RANKING.Weighted"
        assert replaced.description == meta.description

    def test_replace_with_invalid_code_raises(self) -> None:
        meta = DecisionMetadata(**_valid_kwargs())
        with pytest.raises(DecisionValidationError):
            meta.replace(code="")

    def test_decision_validation_error_is_a_validation_error_supertype(self) -> None:
        assert issubclass(DecisionValidationError, ValidationError)
