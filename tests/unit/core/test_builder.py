"""Tests for mineproductivity.core.builder."""

from __future__ import annotations

from typing import Self

import pytest

from mineproductivity.core.builder import BaseBuilder


class GreetingBuilder(BaseBuilder[str]):
    def __init__(self) -> None:
        self._name = "world"

    def with_name(self, name: str) -> Self:
        self._name = name
        return self

    def build(self) -> str:
        if self._name == "fail":
            raise ValueError("boom")
        return f"Hello, {self._name}!"


class TestBaseBuilder:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseBuilder()  # type: ignore[abstract]

    def test_build_produces_object(self) -> None:
        assert GreetingBuilder().with_name("MineProductivity").build() == "Hello, MineProductivity!"

    def test_fluent_chaining_returns_self(self) -> None:
        builder = GreetingBuilder()
        assert builder.with_name("x") is builder

    def test_default_reset_returns_self_noop(self) -> None:
        builder = GreetingBuilder()
        assert builder.reset() is builder


class TestBuildResult:
    def test_returns_ok_on_success(self) -> None:
        result = GreetingBuilder().with_name("core").build_result()
        assert result.is_ok
        assert result.unwrap() == "Hello, core!"

    def test_returns_err_on_exception(self) -> None:
        result = GreetingBuilder().with_name("fail").build_result()
        assert result.is_err
        assert isinstance(result.error, ValueError)
