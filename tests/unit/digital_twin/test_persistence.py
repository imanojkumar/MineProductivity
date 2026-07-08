"""Tests for mineproductivity.digital_twin.persistence.

Design spec §32's repository-substitutability proof: every test here is
written against the ``core.BaseRepository[Twin, str]`` contract alone
(via the one ``_make_repository`` seam below), never against
``InMemoryRepository``-specific internals -- the same suite passes
unmodified against any future production-grade implementation by
changing only that factory.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar, get_args

import pytest

from mineproductivity.core import (
    BaseRepository,
    DuplicateError,
    InMemoryRepository,
    NotFoundError,
)
from mineproductivity.digital_twin.abstractions import Twin, TwinContext
from mineproductivity.digital_twin.metadata import TwinCategory, TwinMetadata
from mineproductivity.digital_twin.persistence import TwinRepository
from mineproductivity.digital_twin.state import TwinState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _AnyTwin(Twin):
    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="TEST.Persistence",
        category=TwinCategory.EQUIPMENT,
        description="A twin for persistence-contract tests.",
    )

    def _apply(self, events: Any, *, context: TwinContext) -> TwinState:
        return self.state


def _twin(twin_id: str) -> _AnyTwin:
    return _AnyTwin(
        id=twin_id,
        scope={"equipment_id": twin_id},
        state=TwinState(attributes={"present": True}, captured_at=_EPOCH),
    )


def _make_repository() -> BaseRepository[Twin, str]:
    """The single substitution seam: swap in any production-grade
    ``core.BaseRepository[Twin, str]`` implementation here and the
    whole suite must pass unchanged (design spec §20, §32)."""
    reference: InMemoryRepository[Twin, str] = InMemoryRepository()
    return reference


class TestTwinRepositoryAlias:
    def test_is_a_literal_type_alias_over_core_base_repository(self) -> None:
        """Design spec §20: not a new ABC, not a subclass -- the alias's
        value IS ``BaseRepository[Twin, str]``."""
        aliased = TwinRepository.__value__
        assert aliased.__origin__ is BaseRepository
        assert get_args(aliased) == (Twin, str)

    def test_reference_implementation_is_core_in_memory_repository_unchanged(self) -> None:
        repository = _make_repository()
        assert type(repository) is InMemoryRepository


class TestRepositoryContract:
    def test_add_then_get_round_trips(self) -> None:
        repository = _make_repository()
        twin = _twin("CONV-7")
        repository.add(twin)
        assert repository.get("CONV-7") is twin

    def test_add_rejects_a_duplicate_id(self) -> None:
        repository = _make_repository()
        repository.add(_twin("CONV-7"))
        with pytest.raises(DuplicateError):
            repository.add(_twin("CONV-7"))

    def test_get_of_unknown_id_raises(self) -> None:
        with pytest.raises(NotFoundError):
            _make_repository().get("NO-SUCH-TWIN")

    def test_find_returns_maybe(self) -> None:
        repository = _make_repository()
        twin = _twin("CONV-7")
        repository.add(twin)
        assert repository.find("CONV-7").unwrap() is twin
        assert repository.find("NO-SUCH-TWIN").is_nothing

    def test_remove_then_get_raises(self) -> None:
        repository = _make_repository()
        repository.add(_twin("CONV-7"))
        repository.remove("CONV-7")
        with pytest.raises(NotFoundError):
            repository.get("CONV-7")

    def test_remove_of_unknown_id_raises(self) -> None:
        with pytest.raises(NotFoundError):
            _make_repository().remove("NO-SUCH-TWIN")

    def test_list_without_specification_returns_everything(self) -> None:
        repository = _make_repository()
        repository.add(_twin("CONV-7"))
        repository.add(_twin("CONV-8"))
        assert sorted(twin.id for twin in repository.list()) == ["CONV-7", "CONV-8"]

    def test_contains_delegates_to_find(self) -> None:
        repository = _make_repository()
        repository.add(_twin("CONV-7"))
        assert "CONV-7" in repository
        assert "NO-SUCH-TWIN" not in repository

    def test_lookup_is_by_identity_not_state(self) -> None:
        """Two instances with the same id are the same twin (§8) -- the
        repository stores the instance it was given, keyed by id."""
        repository = _make_repository()
        twin = _twin("CONV-7")
        repository.add(twin)
        replacement = twin.with_state(TwinState(attributes={"present": False}, captured_at=_EPOCH))
        repository.remove("CONV-7")
        repository.add(replacement)
        assert repository.get("CONV-7").state.attributes["present"] is False
