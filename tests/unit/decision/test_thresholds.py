"""Tests for mineproductivity.decision.thresholds."""

from __future__ import annotations

import pytest

from mineproductivity.decision.exceptions import DecisionValidationError
from mineproductivity.decision.thresholds import Threshold


class TestThresholdConstruction:
    def test_construction(self) -> None:
        threshold = Threshold(field="value", comparator="<", limit=0.65)
        assert threshold.field == "value"
        assert threshold.comparator == "<"
        assert threshold.limit == 0.65

    @pytest.mark.parametrize("comparator", ["<", "<=", ">", ">=", "==", "!="])
    def test_every_documented_comparator_is_accepted(self, comparator: str) -> None:
        threshold = Threshold(field="value", comparator=comparator, limit=1.0)  # type: ignore[arg-type]
        assert threshold.comparator == comparator

    def test_equality_is_value_based(self) -> None:
        first = Threshold(field="value", comparator="<", limit=0.65)
        second = Threshold(field="value", comparator="<", limit=0.65)
        assert first == second


class TestThresholdValidate:
    def test_empty_field_raises(self) -> None:
        with pytest.raises(DecisionValidationError, match="field must not be empty"):
            Threshold(field="", comparator="<", limit=0.65)

    def test_whitespace_only_field_raises(self) -> None:
        with pytest.raises(DecisionValidationError, match="field must not be empty"):
            Threshold(field="   ", comparator="<", limit=0.65)


class TestThresholdReplace:
    def test_replace_reruns_validate(self) -> None:
        threshold = Threshold(field="value", comparator="<", limit=0.65)
        replaced = threshold.replace(limit=0.70)
        assert replaced.limit == 0.70
        assert replaced.field == threshold.field

    def test_replace_with_invalid_field_raises(self) -> None:
        threshold = Threshold(field="value", comparator="<", limit=0.65)
        with pytest.raises(DecisionValidationError):
            threshold.replace(field="")
