"""Tests for mineproductivity.digital_twin.metadata."""

from __future__ import annotations

import pytest

from mineproductivity.core import BaseMetadata
from mineproductivity.digital_twin.exceptions import TwinValidationError
from mineproductivity.digital_twin.metadata import TwinCategory, TwinMetadata


def _meta(code: str = "CONVEYOR.Standard", **overrides: object) -> TwinMetadata:
    fields: dict[str, object] = {
        "code": code,
        "category": TwinCategory.CONVEYOR,
        "description": "x",
    }
    fields.update(overrides)
    return TwinMetadata(**fields)  # type: ignore[arg-type]


class TestTwinCategory:
    def test_exactly_the_eleven_members_of_design_spec_26(self) -> None:
        assert {member.value for member in TwinCategory} == {
            "mine",
            "equipment",
            "plant",
            "conveyor",
            "haulage",
            "fleet",
            "processing_plant",
            "geological",
            "ventilation",
            "stockpile",
            "production",
        }


class TestTwinMetadata:
    def test_subclasses_base_metadata(self) -> None:
        assert issubclass(TwinMetadata, BaseMetadata)

    def test_minimal_valid_construction(self) -> None:
        meta = _meta()
        assert meta.code == "CONVEYOR.Standard"
        assert meta.category is TwinCategory.CONVEYOR
        assert meta.version == "1.0.0"

    def test_name_defaults_to_code(self) -> None:
        assert _meta().name == "CONVEYOR.Standard"

    def test_explicit_name_is_preserved(self) -> None:
        assert _meta(name="Standard conveyor twin").name == "Standard conveyor twin"

    def test_empty_code_raises(self) -> None:
        with pytest.raises(TwinValidationError, match="code must not be empty"):
            _meta(code="")

    def test_whitespace_code_raises(self) -> None:
        with pytest.raises(TwinValidationError, match="code must not be empty"):
            _meta(code="   ")

    def test_non_category_member_raises(self) -> None:
        """Design spec §26/checklist: category must match the closed
        ``TwinCategory`` namespace -- enforced at runtime too, not only
        by the type system."""
        with pytest.raises(TwinValidationError, match="must be a TwinCategory member"):
            _meta(category="conveyor")

    def test_replace_reruns_validation(self) -> None:
        with pytest.raises(TwinValidationError):
            _meta().replace(code="")

    def test_version_is_type_level_semver_independent_of_instances(self) -> None:
        assert _meta(version="2.1.0").version == "2.1.0"
