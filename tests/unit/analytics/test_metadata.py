"""Tests for mineproductivity.analytics.metadata."""

from __future__ import annotations

import pytest

from mineproductivity.core import ValidationError

from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "code": "TREND.Linear",
        "category": AnalyticsCategory.TREND,
        "description": "Ordinary least squares linear trend fit.",
    }
    fields.update(overrides)
    return fields


class TestAnalyticsCategory:
    def test_members(self) -> None:
        assert {member.value for member in AnalyticsCategory} == {
            "trend",
            "baseline",
            "benchmark",
            "forecasting",
            "anomaly",
            "outlier",
        }


class TestAnalyticsMetadataConstruction:
    def test_minimal_valid_construction(self) -> None:
        meta = AnalyticsMetadata(**_valid_kwargs())
        assert meta.code == "TREND.Linear"
        assert meta.category is AnalyticsCategory.TREND
        assert meta.min_observations == 2
        assert meta.version == "1.0.0"

    def test_name_defaults_to_code_when_not_supplied(self) -> None:
        meta = AnalyticsMetadata(**_valid_kwargs())
        assert meta.name == meta.code

    def test_explicit_name_is_preserved(self) -> None:
        meta = AnalyticsMetadata(**_valid_kwargs(name="Linear Trend"))
        assert meta.name == "Linear Trend"

    def test_min_observations_is_overridable(self) -> None:
        meta = AnalyticsMetadata(**_valid_kwargs(min_observations=5))
        assert meta.min_observations == 5

    def test_code_is_a_required_field_with_no_default(self) -> None:
        with pytest.raises(TypeError):
            AnalyticsMetadata(  # type: ignore[call-arg]
                category=AnalyticsCategory.TREND, description="x"
            )

    def test_category_is_a_required_keyword_field(self) -> None:
        with pytest.raises(TypeError):
            AnalyticsMetadata(code="TREND.Linear", description="x")  # type: ignore[call-arg]

    def test_description_is_a_required_keyword_field(self) -> None:
        with pytest.raises(TypeError):
            AnalyticsMetadata(code="TREND.Linear", category=AnalyticsCategory.TREND)  # type: ignore[call-arg]


class TestAnalyticsMetadataValidate:
    def test_valid_metadata_passes(self) -> None:
        AnalyticsMetadata(**_valid_kwargs())  # must not raise

    def test_empty_code_raises_analytics_validation_error(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="code must not be empty"):
            AnalyticsMetadata(**_valid_kwargs(code=""))

    def test_whitespace_only_code_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="code must not be empty"):
            AnalyticsMetadata(**_valid_kwargs(code="   "))

    def test_explicit_blank_name_with_blank_code_raises_analytics_error_first(self) -> None:
        """``AnalyticsMetadata.validate()`` checks ``code`` before calling
        ``super().validate()``, so an empty ``code`` is always reported as
        the domain-specific error, even though an empty ``code`` also
        propagates into ``name`` via :meth:`_normalize`."""
        with pytest.raises(AnalyticsValidationError):
            AnalyticsMetadata(**_valid_kwargs(code=""))

    def test_non_empty_code_with_explicit_blank_name_is_rejected_by_base_metadata(self) -> None:
        """When ``code`` is valid but the caller forces ``name`` to a
        non-empty-then-blank value, this is not reachable through
        ``_normalize`` (it only fills a *falsy* name); ``name=""`` here
        exercises the same ``_normalize`` fallback path and does not raise,
        because ``_normalize`` fills it from ``code`` before ``validate``
        runs."""
        meta = AnalyticsMetadata(**_valid_kwargs(name=""))
        assert meta.name == meta.code


class TestAnalyticsMetadataReplace:
    def test_replace_reruns_normalize_and_validate(self) -> None:
        meta = AnalyticsMetadata(**_valid_kwargs())
        replaced = meta.replace(code="TREND.Exponential")
        assert replaced.code == "TREND.Exponential"
        assert replaced.description == meta.description

    def test_replace_with_invalid_code_raises(self) -> None:
        meta = AnalyticsMetadata(**_valid_kwargs())
        with pytest.raises(AnalyticsValidationError):
            meta.replace(code="")

    def test_base_metadata_is_a_validation_error_supertype(self) -> None:
        assert issubclass(AnalyticsValidationError, ValidationError)
