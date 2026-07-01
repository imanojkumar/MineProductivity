"""Tests for mineproductivity.core.repository."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core.entity import BaseEntity
from mineproductivity.core.exceptions import DuplicateError, NotFoundError
from mineproductivity.core.repository import BaseRepository, InMemoryRepository
from mineproductivity.core.specification import BaseSpecification


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Item(BaseEntity[str]):
    name: str
    active: bool = True


class IsActive(BaseSpecification[Item]):
    def is_satisfied_by(self, candidate: Item) -> bool:
        return candidate.active


@pytest.fixture
def repo() -> InMemoryRepository[Item, str]:
    return InMemoryRepository()


class TestBaseRepository:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseRepository()  # type: ignore[abstract]


class TestAdd:
    def test_add_then_get_round_trips(self, repo: InMemoryRepository[Item, str]) -> None:
        repo.add(Item(id="1", name="widget"))
        assert repo.get("1").name == "widget"

    def test_add_duplicate_id_raises(self, repo: InMemoryRepository[Item, str]) -> None:
        repo.add(Item(id="1", name="widget"))
        with pytest.raises(DuplicateError):
            repo.add(Item(id="1", name="other"))


class TestGet:
    def test_get_missing_raises_not_found(self, repo: InMemoryRepository[Item, str]) -> None:
        with pytest.raises(NotFoundError):
            repo.get("missing")


class TestFind:
    def test_find_existing_returns_some(self, repo: InMemoryRepository[Item, str]) -> None:
        repo.add(Item(id="1", name="widget"))
        found = repo.find("1")
        assert found.is_some
        assert found.unwrap().name == "widget"

    def test_find_missing_returns_nothing(self, repo: InMemoryRepository[Item, str]) -> None:
        assert repo.find("missing").is_nothing


class TestRemove:
    def test_remove_existing(self, repo: InMemoryRepository[Item, str]) -> None:
        repo.add(Item(id="1", name="widget"))
        repo.remove("1")
        assert repo.find("1").is_nothing

    def test_remove_missing_raises_not_found(self, repo: InMemoryRepository[Item, str]) -> None:
        with pytest.raises(NotFoundError):
            repo.remove("missing")


class TestList:
    def test_list_returns_all_entities(self, repo: InMemoryRepository[Item, str]) -> None:
        repo.add(Item(id="1", name="a"))
        repo.add(Item(id="2", name="b"))
        assert {item.id for item in repo.list()} == {"1", "2"}

    def test_list_empty_repository(self, repo: InMemoryRepository[Item, str]) -> None:
        assert repo.list() == []

    def test_list_filters_by_specification(self, repo: InMemoryRepository[Item, str]) -> None:
        repo.add(Item(id="1", name="a", active=True))
        repo.add(Item(id="2", name="b", active=False))
        active_items = repo.list(IsActive())
        assert [item.id for item in active_items] == ["1"]


class TestContains:
    def test_contains_true_for_existing_id(self, repo: InMemoryRepository[Item, str]) -> None:
        repo.add(Item(id="1", name="a"))
        assert "1" in repo

    def test_contains_false_for_missing_id(self, repo: InMemoryRepository[Item, str]) -> None:
        assert "missing" not in repo
