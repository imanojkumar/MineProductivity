"""Tests for mineproductivity.registry.registry."""

from __future__ import annotations

from mineproductivity.core import BaseMetadata, PredicateSpecification
from mineproductivity.registry.exceptions import DuplicateRegistrationError, UnregisteredLookupError
from mineproductivity.registry.registry import Registry


class _Widget:
    pass


class _OtherWidget:
    pass


class TestConstruction:
    def test_name_property(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        assert registry.name == "widgets"

    def test_starts_empty(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        assert len(registry) == 0
        assert list(registry) == []


class TestRegister:
    def test_register_returns_ok(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        result = registry.register("widget", _Widget)
        assert result.is_ok

    def test_register_makes_item_retrievable(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        registry.register("widget", _Widget)
        assert registry.get("widget") is _Widget

    def test_duplicate_key_rejected(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        registry.register("widget", _Widget)
        result = registry.register("widget", _OtherWidget)
        assert result.is_err
        assert isinstance(result.error, DuplicateRegistrationError)

    def test_duplicate_key_does_not_overwrite(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        registry.register("widget", _Widget)
        registry.register("widget", _OtherWidget)
        assert registry.get("widget") is _Widget

    def test_register_with_metadata(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        meta = BaseMetadata(name="Widget")
        registry.register("widget", _Widget, metadata=meta)
        assert registry.metadata_for("widget").unwrap() is meta

    def test_register_without_metadata_leaves_metadata_absent(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        registry.register("widget", _Widget)
        assert registry.metadata_for("widget").is_nothing


class TestLookup:
    def test_lookup_found(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        registry.register("widget", _Widget)
        assert registry.lookup("widget").unwrap() is _Widget

    def test_lookup_missing_returns_nothing(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        assert registry.lookup("missing").is_nothing


class TestGet:
    def test_get_found(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        registry.register("widget", _Widget)
        assert registry.get("widget") is _Widget

    def test_get_missing_raises(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        try:
            registry.get("missing")
        except UnregisteredLookupError:
            pass
        else:
            raise AssertionError("expected UnregisteredLookupError")


class TestList:
    def test_list_all(self) -> None:
        registry: Registry[str, int] = Registry(name="numbers")
        for i in range(5):
            registry.register(str(i), i)
        assert sorted(registry.list()) == [0, 1, 2, 3, 4]

    def test_list_with_specification(self) -> None:
        registry: Registry[str, int] = Registry(name="numbers")
        for i in range(5):
            registry.register(str(i), i)
        evens = registry.list(PredicateSpecification(lambda n: n % 2 == 0))
        assert sorted(evens) == [0, 2, 4]

    def test_list_empty_registry(self) -> None:
        registry: Registry[str, int] = Registry(name="numbers")
        assert registry.list() == []


class TestContainerProtocol:
    def test_contains(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        registry.register("widget", _Widget)
        assert "widget" in registry
        assert "missing" not in registry

    def test_len(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        assert len(registry) == 0
        registry.register("widget", _Widget)
        assert len(registry) == 1

    def test_iter_yields_keys(self) -> None:
        registry: Registry[str, type] = Registry(name="widgets")
        registry.register("a", _Widget)
        registry.register("b", _OtherWidget)
        assert set(registry) == {"a", "b"}
