"""Tests for mineproductivity.core.factory."""

from __future__ import annotations

from typing import Any

import pytest

from mineproductivity.core.factory import BaseFactory


class GreetingFactory(BaseFactory[str]):
    def create(self, **kwargs: Any) -> str:
        name = kwargs.get("name", "world")
        if name == "fail":
            raise ValueError("boom")
        return f"Hello, {name}!"


class TestBaseFactory:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseFactory()  # type: ignore[abstract]

    def test_create_returns_object(self) -> None:
        assert GreetingFactory().create(name="MineProductivity") == "Hello, MineProductivity!"

    def test_create_uses_default_when_no_kwargs(self) -> None:
        assert GreetingFactory().create() == "Hello, world!"


class TestCreateResult:
    def test_returns_ok_on_success(self) -> None:
        result = GreetingFactory().create_result(name="core")
        assert result.is_ok
        assert result.unwrap() == "Hello, core!"

    def test_returns_err_on_exception(self) -> None:
        result = GreetingFactory().create_result(name="fail")
        assert result.is_err
        assert isinstance(result.error, ValueError)
