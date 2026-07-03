"""Tests for mineproductivity.registry.decorators."""

from __future__ import annotations

from mineproductivity.core import BaseMetadata
from mineproductivity.registry.decorators import registered_in
from mineproductivity.registry.registry import Registry


class TestRegisteredIn:
    def test_decorator_registers_item_by_derived_key(self) -> None:
        registry: Registry[str, type] = Registry(name="kpis")
        register = registered_in(registry, key_of=lambda cls: cls.__name__)

        @register
        class FuelPerTonne:
            pass

        assert registry.get("FuelPerTonne") is FuelPerTonne

    def test_decorator_returns_the_original_item_unchanged(self) -> None:
        registry: Registry[str, type] = Registry(name="kpis")
        register = registered_in(registry, key_of=lambda cls: cls.__name__)

        class FuelPerTonne:
            pass

        decorated = register(FuelPerTonne)
        assert decorated is FuelPerTonne

    def test_decorator_attaches_derived_metadata(self) -> None:
        class Widget:
            meta = BaseMetadata(name="Widget")

        registry: Registry[str, type[Widget]] = Registry(name="kpis")
        register = registered_in(
            registry,
            key_of=lambda cls: cls.__name__,
            metadata_of=lambda cls: cls.meta,
        )
        register(Widget)

        assert registry.metadata_for("Widget").unwrap() is Widget.meta

    def test_decorator_without_metadata_of_registers_no_metadata(self) -> None:
        registry: Registry[str, type] = Registry(name="kpis")
        register = registered_in(registry, key_of=lambda cls: cls.__name__)

        class Widget:
            pass

        register(Widget)

        assert registry.metadata_for("Widget").is_nothing

    def test_two_decorated_items_both_registered(self) -> None:
        registry: Registry[str, type] = Registry(name="kpis")
        register = registered_in(registry, key_of=lambda cls: cls.__name__)

        @register
        class A:
            pass

        @register
        class B:
            pass

        assert len(registry) == 2
        assert registry.get("A") is A
        assert registry.get("B") is B
