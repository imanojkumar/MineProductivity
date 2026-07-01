"""Tests for mineproductivity.core.result."""

from __future__ import annotations

import pytest

from mineproductivity.core.exceptions import MineProductivityError
from mineproductivity.core.result import Result


def divide(a: float, b: float) -> Result[float]:
    if b == 0:
        return Result.err("division by zero")
    return Result.ok(a / b)


class TestConstruction:
    def test_ok_is_ok(self) -> None:
        result = Result.ok(5)
        assert result.is_ok is True
        assert result.is_err is False

    def test_err_is_err(self) -> None:
        result: Result[int] = Result.err("boom")
        assert result.is_err is True
        assert result.is_ok is False

    def test_err_wraps_string_in_mineproductivity_error(self) -> None:
        result: Result[int] = Result.err("boom")
        assert isinstance(result.error, MineProductivityError)
        assert result.error.message == "boom"

    def test_err_accepts_exception_instance(self) -> None:
        exc = ValueError("bad value")
        result: Result[int] = Result.err(exc)
        assert result.error is exc

    def test_direct_construction_with_conflicting_state_raises(self) -> None:
        with pytest.raises(ValueError):
            Result(_value=1, _error=ValueError("x"), _is_ok=True)

    def test_direct_construction_err_without_error_raises(self) -> None:
        with pytest.raises(ValueError):
            Result(_value=None, _error=None, _is_ok=False)


class TestAccessors:
    def test_value_on_ok_returns_value(self) -> None:
        assert Result.ok(5).value == 5

    def test_value_on_err_raises_stored_error(self) -> None:
        result: Result[int] = Result.err("boom")
        with pytest.raises(MineProductivityError, match="boom"):
            _ = result.value

    def test_error_on_ok_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _ = Result.ok(5).error

    def test_unwrap_is_alias_for_value(self) -> None:
        assert Result.ok(5).unwrap() == 5

    def test_unwrap_or_returns_default_on_err(self) -> None:
        assert divide(10, 0).unwrap_or(0.0) == 0.0

    def test_unwrap_or_returns_value_on_ok(self) -> None:
        assert divide(10, 2).unwrap_or(0.0) == 5.0

    def test_unwrap_or_else_invoked_only_on_err(self) -> None:
        assert divide(10, 0).unwrap_or_else(lambda e: -1.0) == -1.0
        assert divide(10, 2).unwrap_or_else(lambda e: -1.0) == 5.0


class TestCombinators:
    def test_map_transforms_ok_value(self) -> None:
        assert divide(10, 2).map(lambda x: x * 2).unwrap() == 10.0

    def test_map_is_noop_on_err(self) -> None:
        result = divide(10, 0).map(lambda x: x * 2)
        assert result.is_err

    def test_map_err_transforms_error(self) -> None:
        result = divide(10, 0).map_err(lambda e: MineProductivityError(f"wrapped: {e}"))
        assert "wrapped" in str(result.error)

    def test_map_err_is_noop_on_ok(self) -> None:
        result = divide(10, 2).map_err(lambda e: MineProductivityError("never"))
        assert result.unwrap() == 5.0

    def test_and_then_chains_on_ok(self) -> None:
        result = divide(10, 2).and_then(lambda v: divide(v, 5))
        assert result.unwrap() == 1.0

    def test_and_then_short_circuits_on_err(self) -> None:
        result = divide(10, 0).and_then(lambda v: divide(v, 5))
        assert result.is_err


class TestDunder:
    def test_bool_true_for_ok(self) -> None:
        assert bool(Result.ok(1)) is True

    def test_bool_false_for_err(self) -> None:
        assert bool(Result.err("x")) is False

    def test_repr_ok(self) -> None:
        assert repr(Result.ok(1)) == "Result.ok(1)"

    def test_repr_err(self) -> None:
        assert "Result.err(" in repr(Result.err("x"))
