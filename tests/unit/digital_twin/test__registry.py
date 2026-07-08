"""Tests for mineproductivity.digital_twin._registry.

Mirrors ``tests/unit/decision/test__registry.py``'s scope exactly --
``digital_twin.REGISTRY``/``register`` specialize ``registry.Registry``
the same way ``decision._registry`` does one layer down. Unlike
``decision``/``analytics``, this package deliberately ships **zero**
registered built-in twin types (a concrete twin type is a site-specific
modeling choice, design spec §27.1), proven below by a mechanical scan
rather than a registration-order-dependent emptiness assertion.

Entry-point discovery/isolation against real installed plugin packages
(the healthy/broken fixture-plugin pattern) is already covered
generically, once, in
``tests/integration/test_registry_plugin_discovery.py`` -- the
mechanism (``EntryPointDiscovery``/``EntryPointSpec``) is identical
regardless of which ``Registry`` it targets
(``EntryPointSpec(group="mineproductivity.digital_twin", target_registry="digital_twin")``
goes through the exact same per-entry-point isolation code path, spec
03 §11), so a second, Twin-specific copy of that same test would add no
incremental coverage -- the same reasoning that keeps ``kpis``,
``analytics``, and ``decision`` from having their own copies either.
What *is* Twin-specific -- ``register``'s translation of a
duplicate/empty code into this package's own exception types -- is
exercised below. ``examples/digital_twin/04_plugin_twin_type.py``
additionally demonstrates the full third-party entry-point wiring end
to end.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar

import pytest

import mineproductivity.digital_twin as digital_twin
from mineproductivity.digital_twin._registry import REGISTRY, register
from mineproductivity.digital_twin.abstractions import Twin, TwinContext
from mineproductivity.digital_twin.exceptions import (
    TwinValidationError,
    TwinVersionConflictError,
)
from mineproductivity.digital_twin.metadata import TwinCategory, TwinMetadata
from mineproductivity.digital_twin.state import TwinState
from mineproductivity.registry import UnregisteredLookupError

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _meta(code: str) -> TwinMetadata:
    return TwinMetadata(code=code, category=TwinCategory.EQUIPMENT, description="x")


def _unique_code() -> str:
    return f"TEST.RegistryTwin{uuid.uuid4().hex}"


class _FixtureTwin(Twin):
    def _apply(self, events: Any, *, context: TwinContext) -> TwinState:
        return TwinState(attributes={"seen": len(events)}, captured_at=_EPOCH)


class TestNoBuiltInTwinTypesShipped:
    def test_no_module_in_the_package_registers_a_twin_type(self) -> None:
        """Design spec §27.1: a concrete twin type is an extension, not
        a built-in -- mechanically, no ``@register``/``register(`` use
        exists anywhere in ``src/mineproductivity/digital_twin/``."""
        package_dir = Path(digital_twin.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "_registry.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            assert "@register" not in source, f"{py_file.name} registers a built-in twin type"


class TestRegistryGetUnknownCode:
    def test_raises_unregistered_lookup_error(self) -> None:
        with pytest.raises(UnregisteredLookupError):
            REGISTRY.get("NOT.AReal.Code")


class TestRegisterDecorator:
    def test_registers_a_new_twin_type(self) -> None:
        code = _unique_code()

        @register
        class _NewFixture(_FixtureTwin):
            meta: ClassVar[TwinMetadata] = _meta(code)

        assert REGISTRY.get(code) is _NewFixture

    def test_registry_metadata_matches_the_class_own_meta(self) -> None:
        code = _unique_code()

        @register
        class _Fixture(_FixtureTwin):
            meta: ClassVar[TwinMetadata] = _meta(code)

        assert REGISTRY.metadata_for(code).unwrap() is _Fixture.meta

    def test_returns_the_class_unchanged(self) -> None:
        class _Fixture(_FixtureTwin):
            meta: ClassVar[TwinMetadata] = _meta(_unique_code())

        assert register(_Fixture) is _Fixture

    def test_empty_code_raises_twin_validation_error(self) -> None:
        """A real ``TwinMetadata`` can never carry an empty ``code``
        (its own ``validate()`` rejects it before ``register`` is ever
        reached), so ``register``'s own defensive empty-code guard is
        exercised via a minimal ``meta`` stand-in that bypasses
        ``TwinMetadata`` construction entirely -- the same technique
        every sibling package's registry tests use."""

        class _FakeMeta:
            code = ""

        class _Fixture(_FixtureTwin):
            meta = _FakeMeta()  # type: ignore[assignment]

        with pytest.raises(TwinValidationError):
            register(_Fixture)

    def test_duplicate_code_raises_version_conflict(self) -> None:
        code = _unique_code()

        @register
        class _First(_FixtureTwin):
            meta: ClassVar[TwinMetadata] = _meta(code)

        class _Second(_FixtureTwin):
            meta: ClassVar[TwinMetadata] = _meta(code)

        with pytest.raises(TwinVersionConflictError):
            register(_Second)

    def test_duplicate_code_rejected_even_with_identical_metadata(self) -> None:
        """``Registry.register`` is add-only and rejects *any*
        re-registration under an existing key, identical item or not
        (design spec AD-RG-04) -- raised at registration time, never
        deferred (§21)."""
        shared_meta = _meta(_unique_code())

        class _First(_FixtureTwin):
            meta: ClassVar[TwinMetadata] = shared_meta

        register(_First)

        class _Second(_FixtureTwin):
            meta: ClassVar[TwinMetadata] = shared_meta

        with pytest.raises(TwinVersionConflictError):
            register(_Second)
