"""Tests for mineproductivity.core.metadata.

Note: ``tags`` is typed as ``frozenset[str]`` (its canonical stored form),
but the constructor also accepts any iterable at runtime via
``_normalize()``. Passing a plain ``list`` below is intentional -- it
exercises that runtime convenience -- so those call sites carry an
explicit ``# type: ignore[arg-type]``.
"""

from __future__ import annotations

from types import MappingProxyType

import pytest

from mineproductivity.core.exceptions import ValidationError
from mineproductivity.core.metadata import BaseMetadata


class TestConstruction:
    def test_minimal_construction(self) -> None:
        meta = BaseMetadata(name="example")
        assert meta.name == "example"
        assert meta.description == ""
        assert meta.tags == frozenset()
        assert meta.attributes == {}

    def test_full_construction(self) -> None:
        meta = BaseMetadata(
            name="example",
            description="a description",
            tags=["a", "b"],  # type: ignore[arg-type]
            attributes={"k": 1},
        )
        assert meta.description == "a description"
        assert meta.tags == frozenset({"a", "b"})
        assert meta.attributes["k"] == 1


class TestValidation:
    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BaseMetadata(name="")

    def test_whitespace_only_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BaseMetadata(name="   ")


class TestImmutability:
    def test_tags_are_frozen(self) -> None:
        meta = BaseMetadata(name="example", tags=["a", "b"])  # type: ignore[arg-type]
        assert isinstance(meta.tags, frozenset)

    def test_attributes_are_read_only(self) -> None:
        meta = BaseMetadata(name="example", attributes={"k": 1})
        assert isinstance(meta.attributes, MappingProxyType)
        with pytest.raises(TypeError):
            meta.attributes["k"] = 2  # type: ignore[index]

    def test_mutating_source_list_after_construction_does_not_affect_instance(self) -> None:
        source_tags = ["a"]
        source_attrs = {"k": 1}
        meta = BaseMetadata(
            name="example",
            tags=source_tags,  # type: ignore[arg-type]
            attributes=source_attrs,
        )
        source_tags.append("b")
        source_attrs["k"] = 999
        assert meta.tags == frozenset({"a"})
        assert meta.attributes["k"] == 1


class TestEquality:
    def test_equal_metadata_are_equal(self) -> None:
        a = BaseMetadata(name="x", tags=["a"], attributes={"k": 1})  # type: ignore[arg-type]
        b = BaseMetadata(name="x", tags=["a"], attributes={"k": 1})  # type: ignore[arg-type]
        assert a == b
