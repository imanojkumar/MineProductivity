"""Tests for mineproductivity.core.value_object."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core.value_object import BaseValueObject


@dataclasses.dataclass(frozen=True, slots=True)
class Money(BaseValueObject):
    amount: int
    currency: str

    def validate(self) -> None:
        if self.amount < 0:
            raise ValueError("amount must be non-negative")


@dataclasses.dataclass(frozen=True, slots=True)
class Tags(BaseValueObject):
    values: tuple[str, ...] = ()

    def _normalize(self) -> None:
        object.__setattr__(self, "values", tuple(self.values))


class TestEquality:
    def test_equal_fields_are_equal(self) -> None:
        assert Money(10, "USD") == Money(10, "USD")

    def test_different_fields_are_not_equal(self) -> None:
        assert Money(10, "USD") != Money(20, "USD")

    def test_different_type_is_not_equal(self) -> None:
        assert Money(10, "USD") != object()

    def test_equal_instances_hash_equal(self) -> None:
        assert hash(Money(10, "USD")) == hash(Money(10, "USD"))

    def test_usable_as_dict_key(self) -> None:
        d = {Money(10, "USD"): "ten dollars"}
        assert d[Money(10, "USD")] == "ten dollars"


class TestImmutability:
    def test_field_assignment_raises(self) -> None:
        money = Money(10, "USD")
        with pytest.raises(dataclasses.FrozenInstanceError):
            money.amount = 20  # type: ignore[misc]

    def test_replace_returns_new_instance(self) -> None:
        money = Money(10, "USD")
        updated = money.replace(amount=20)
        assert updated is not money
        assert updated == Money(20, "USD")
        assert money == Money(10, "USD")


class TestValidation:
    def test_invalid_construction_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            Money(-1, "USD")

    def test_invalid_replace_raises(self) -> None:
        money = Money(10, "USD")
        with pytest.raises(ValueError, match="non-negative"):
            money.replace(amount=-5)

    def test_base_class_default_validate_is_noop(self) -> None:
        @dataclasses.dataclass(frozen=True, slots=True)
        class Plain(BaseValueObject):
            x: int

        assert Plain(1).x == 1


class TestNormalize:
    def test_normalize_runs_before_validate(self) -> None:
        # Deliberately passing a list where a tuple is declared, to exercise
        # _normalize()'s runtime coercion; the field is typed as the
        # canonical stored form, not every acceptable constructor input.
        tags = Tags(values=["a", "b"])  # type: ignore[arg-type]
        assert tags.values == ("a", "b")

    def test_normalize_applies_on_replace(self) -> None:
        tags = Tags()
        updated = tags.replace(values=["x"])
        assert updated.values == ("x",)
