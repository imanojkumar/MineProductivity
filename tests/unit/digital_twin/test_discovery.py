"""Tests for mineproductivity.digital_twin.discovery."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar

from mineproductivity.core import InMemoryRepository
from mineproductivity.digital_twin.abstractions import Twin, TwinContext
from mineproductivity.digital_twin.categories import ConveyorTwin, StockpileTwin
from mineproductivity.digital_twin.discovery import by_category, by_scope
from mineproductivity.digital_twin.metadata import TwinCategory, TwinMetadata
from mineproductivity.digital_twin.state import TwinState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _BeltTwin(ConveyorTwin):
    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="CONVEYOR.DiscoveryBelt",
        category=TwinCategory.CONVEYOR,
        description="A belt conveyor twin.",
    )

    def _apply(self, events: Any, *, context: TwinContext) -> TwinState:
        return self.state


class _PileTwin(StockpileTwin):
    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="STOCKPILE.DiscoveryPile",
        category=TwinCategory.STOCKPILE,
        description="A stockpile twin.",
    )

    def _apply(self, events: Any, *, context: TwinContext) -> TwinState:
        return self.state


def _state() -> TwinState:
    return TwinState(attributes={"present": True}, captured_at=_EPOCH)


def _populated_repository() -> InMemoryRepository[Twin, str]:
    repository: InMemoryRepository[Twin, str] = InMemoryRepository()
    repository.add(
        _BeltTwin(id="CONV-7", scope={"equipment_id": "CONV-7", "pit": "north"}, state=_state())
    )
    repository.add(
        _BeltTwin(id="CONV-8", scope={"equipment_id": "CONV-8", "pit": "south"}, state=_state())
    )
    repository.add(
        _PileTwin(id="SP-1", scope={"stockpile_id": "SP-1", "pit": "north"}, state=_state())
    )
    return repository


class TestByCategory:
    def test_matches_only_the_requested_category(self) -> None:
        repository = _populated_repository()
        conveyors = repository.list(by_category(TwinCategory.CONVEYOR))
        assert sorted(twin.id for twin in conveyors) == ["CONV-7", "CONV-8"]

    def test_empty_result_is_an_empty_sequence_never_a_raise(self) -> None:
        """Design spec §18: there is no ``TwinNotFoundError`` path
        through discovery at all."""
        repository = _populated_repository()
        assert list(repository.list(by_category(TwinCategory.VENTILATION))) == []


class TestByScope:
    def test_subset_match_over_the_twin_scope(self) -> None:
        repository = _populated_repository()
        north = repository.list(by_scope({"pit": "north"}))
        assert sorted(twin.id for twin in north) == ["CONV-7", "SP-1"]

    def test_every_requested_key_must_match(self) -> None:
        repository = _populated_repository()
        exact = repository.list(by_scope({"pit": "north", "equipment_id": "CONV-7"}))
        assert [twin.id for twin in exact] == ["CONV-7"]

    def test_key_absent_from_a_twin_scope_excludes_it(self) -> None:
        repository = _populated_repository()
        assert list(repository.list(by_scope({"shift": "A"}))) == []

    def test_requested_scope_is_copied_not_aliased(self) -> None:
        wanted = {"pit": "north"}
        specification = by_scope(wanted)
        wanted["pit"] = "south"
        repository = _populated_repository()
        assert sorted(twin.id for twin in repository.list(specification)) == ["CONV-7", "SP-1"]


class TestComposition:
    def test_specifications_compose_with_the_core_operators(self) -> None:
        """Design spec §18's own worked composition:
        ``by_category(...) & by_scope(...)``."""
        repository = _populated_repository()
        matched = repository.list(by_category(TwinCategory.CONVEYOR) & by_scope({"pit": "north"}))
        assert [twin.id for twin in matched] == ["CONV-7"]

    def test_negation_composes_too(self) -> None:
        repository = _populated_repository()
        matched = repository.list(~by_category(TwinCategory.CONVEYOR))
        assert [twin.id for twin in matched] == ["SP-1"]
