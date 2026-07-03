"""Tests for the mineproductivity.core package's public API surface.

These tests guard the "beautiful public API" requirement: everything a
consumer needs must be importable directly from ``mineproductivity.core``
without reaching into internal modules, and ``__all__`` must not drift
from what is actually exported.
"""

from __future__ import annotations

import importlib

import mineproductivity.core as core


class TestPublicApiSurface:
    def test_all_entries_are_actually_importable_attributes(self) -> None:
        for name in core.__all__:
            assert hasattr(core, name), f"{name!r} listed in __all__ but not defined"

    def test_no_duplicate_entries_in_all(self) -> None:
        assert len(core.__all__) == len(set(core.__all__))

    def test_all_is_sorted(self) -> None:
        assert list(core.__all__) == sorted(core.__all__)

    def test_direct_import_of_base_classes(self) -> None:
        from mineproductivity.core import BaseEntity, BaseRepository, BaseValueObject, Result

        assert BaseEntity is not None
        assert BaseRepository is not None
        assert BaseValueObject is not None
        assert Result is not None


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "builder",
            "configuration",
            "entity",
            "exceptions",
            "factory",
            "identifier",
            "maybe",
            "metadata",
            "repository",
            "result",
            "serialization",
            "service",
            "specification",
            "typing",
            "validator",
            "value_object",
            "versioning",
        ]
        for name in submodules:
            module = importlib.import_module(f"mineproductivity.core.{name}")
            assert module is not None

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(core)


class TestPackageVersion:
    def test_top_level_package_exposes_version(self) -> None:
        import mineproductivity

        assert mineproductivity.__version__ == "0.7.0"

    def test_core_has_no_dependency_on_sibling_packages(self) -> None:
        import ast
        from pathlib import Path

        core_dir = Path(core.__file__).parent
        for py_file in core_dir.glob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert not node.module.startswith(
                        "mineproductivity."
                    ) or node.module.startswith("mineproductivity.core"), (
                        f"{py_file.name} imports from sibling package {node.module!r}"
                    )
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith(
                            "mineproductivity."
                        ) or alias.name.startswith("mineproductivity.core"), (
                            f"{py_file.name} imports sibling package {alias.name!r}"
                        )
