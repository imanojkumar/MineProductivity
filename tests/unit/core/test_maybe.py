"""Tests for mineproductivity.core.maybe."""

from __future__ import annotations

import pytest

from mineproductivity.core.maybe import Maybe


def find_even(values: list[int]) -> Maybe[int]:
    for value in values:
        if value % 2 == 0:
            return Maybe.some(value)
    return Maybe.nothing()


class TestConstruction:
    def test_some_is_some(self) -> None:
        maybe = Maybe.some(5)
        assert maybe.is_some is True
        assert maybe.is_nothing is False

    def test_nothing_is_nothing(self) -> None:
        maybe: Maybe[int] = Maybe.nothing()
        assert maybe.is_nothing is True
        assert maybe.is_some is False

    def test_some_can_hold_falsy_value(self) -> None:
        maybe = Maybe.some(0)
        assert maybe.is_some is True
        assert maybe.unwrap() == 0


class TestAccessors:
    def test_unwrap_some_returns_value(self) -> None:
        assert Maybe.some(5).unwrap() == 5

    def test_unwrap_nothing_raises(self) -> None:
        with pytest.raises(ValueError):
            Maybe.nothing().unwrap()

    def test_unwrap_or_returns_value_when_some(self) -> None:
        assert find_even([1, 3, 4]).unwrap_or(-1) == 4

    def test_unwrap_or_returns_default_when_nothing(self) -> None:
        assert find_even([1, 3, 5]).unwrap_or(-1) == -1

    def test_unwrap_or_else_invoked_only_when_nothing(self) -> None:
        assert Maybe[int].nothing().unwrap_or_else(lambda: 42) == 42
        assert Maybe.some(1).unwrap_or_else(lambda: 42) == 1


class TestCombinators:
    def test_map_transforms_value(self) -> None:
        assert Maybe.some(2).map(lambda x: x * 10).unwrap() == 20

    def test_map_is_noop_on_nothing(self) -> None:
        assert Maybe.nothing().map(lambda x: x * 10).is_nothing

    def test_and_then_chains_when_some(self) -> None:
        result = Maybe.some(2).and_then(lambda x: Maybe.some(x * 10))
        assert result.unwrap() == 20

    def test_and_then_short_circuits_on_nothing(self) -> None:
        result: Maybe[int] = Maybe.nothing()
        assert result.and_then(lambda x: Maybe.some(x * 10)).is_nothing

    def test_filter_keeps_matching_value(self) -> None:
        assert Maybe.some(4).filter(lambda x: x > 0).is_some

    def test_filter_drops_non_matching_value(self) -> None:
        assert Maybe.some(-4).filter(lambda x: x > 0).is_nothing

    def test_filter_on_nothing_stays_nothing(self) -> None:
        assert Maybe.nothing().filter(lambda x: True).is_nothing

    def test_to_result_some_becomes_ok(self) -> None:
        result = Maybe.some(5).to_result("missing")
        assert result.is_ok
        assert result.unwrap() == 5

    def test_to_result_nothing_becomes_err(self) -> None:
        result: Maybe[int] = Maybe.nothing()
        assert result.to_result("missing").is_err


class TestDunder:
    def test_bool_true_for_some(self) -> None:
        assert bool(Maybe.some(1)) is True

    def test_bool_false_for_nothing(self) -> None:
        assert bool(Maybe.nothing()) is False

    def test_repr_some(self) -> None:
        assert repr(Maybe.some(1)) == "Maybe.some(1)"

    def test_repr_nothing(self) -> None:
        assert repr(Maybe.nothing()) == "Maybe.nothing()"
