"""Tests for mineproductivity.core.specification."""

from __future__ import annotations

import pytest

from mineproductivity.core.specification import (
    AndSpecification,
    BaseSpecification,
    NotSpecification,
    OrSpecification,
    PredicateSpecification,
)


class IsPositive(BaseSpecification[int]):
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > 0


class IsEven(BaseSpecification[int]):
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate % 2 == 0


class TestBaseSpecification:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseSpecification()  # type: ignore[abstract]

    def test_call_delegates_to_is_satisfied_by(self) -> None:
        spec = IsPositive()
        assert spec(1) is True
        assert spec(-1) is False


class TestAndSpecification:
    def test_and_true_when_both_true(self) -> None:
        spec = IsPositive() & IsEven()
        assert isinstance(spec, AndSpecification)
        assert spec.is_satisfied_by(4) is True

    def test_and_false_when_either_false(self) -> None:
        spec = IsPositive() & IsEven()
        assert spec.is_satisfied_by(3) is False
        assert spec.is_satisfied_by(-4) is False


class TestOrSpecification:
    def test_or_true_when_either_true(self) -> None:
        spec = IsPositive() | IsEven()
        assert isinstance(spec, OrSpecification)
        assert spec.is_satisfied_by(-4) is True
        assert spec.is_satisfied_by(3) is True

    def test_or_false_when_both_false(self) -> None:
        spec = IsPositive() | IsEven()
        assert spec.is_satisfied_by(-3) is False


class TestNotSpecification:
    def test_negates_wrapped_specification(self) -> None:
        spec = ~IsPositive()
        assert isinstance(spec, NotSpecification)
        assert spec.is_satisfied_by(-1) is True
        assert spec.is_satisfied_by(1) is False


class TestPredicateSpecification:
    def test_wraps_plain_callable(self) -> None:
        adult: PredicateSpecification[int] = PredicateSpecification(lambda age: age >= 18)
        assert adult.is_satisfied_by(21) is True
        assert adult.is_satisfied_by(10) is False

    def test_composable_with_class_based_specifications(self) -> None:
        big: PredicateSpecification[int] = PredicateSpecification(lambda x: x > 100)
        spec = IsPositive() & big
        assert spec.is_satisfied_by(101) is True
        assert spec.is_satisfied_by(50) is False


class TestComposition:
    def test_deeply_nested_composition(self) -> None:
        spec = (IsPositive() & IsEven()) | ~IsPositive()
        assert spec.is_satisfied_by(4) is True
        assert spec.is_satisfied_by(-1) is True
        assert spec.is_satisfied_by(3) is False
