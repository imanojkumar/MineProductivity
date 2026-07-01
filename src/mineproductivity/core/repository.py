"""``BaseRepository``: the abstract collection-like contract for aggregate persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable, Sequence
from typing import Any, Generic, TypeVar

from mineproductivity.core.entity import BaseEntity
from mineproductivity.core.exceptions import DuplicateError, NotFoundError
from mineproductivity.core.maybe import Maybe
from mineproductivity.core.specification import BaseSpecification

__all__ = ["BaseRepository", "InMemoryRepository"]

TId = TypeVar("TId", bound=Hashable)
TEntity = TypeVar("TEntity", bound=BaseEntity[Any])


class BaseRepository(ABC, Generic[TEntity, TId]):
    """The abstract contract for storing and retrieving
    :class:`~mineproductivity.core.entity.BaseEntity` aggregates by
    identity, independent of the underlying storage technology.

    ``core`` defines only the contract; concrete persistence (SQL,
    document store, remote API) belongs in the package that needs it and
    depends on ``core.repository``, never the other way around
    (Dependency Inversion Principle). :class:`InMemoryRepository` is the
    one concrete implementation provided here, intended for tests and
    examples rather than production persistence.
    """

    @abstractmethod
    def add(self, entity: TEntity) -> None:
        """Persist a new ``entity``.

        Raises
        ------
        DuplicateError
            If an entity with the same id already exists.
        """

    @abstractmethod
    def get(self, entity_id: TId) -> TEntity:
        """Return the entity with ``entity_id``.

        Raises
        ------
        NotFoundError
            If no such entity exists.
        """

    @abstractmethod
    def find(self, entity_id: TId) -> Maybe[TEntity]:
        """Return :meth:`Maybe.some` the entity, or :meth:`Maybe.nothing`
        if no entity with ``entity_id`` exists."""

    @abstractmethod
    def remove(self, entity_id: TId) -> None:
        """Remove the entity with ``entity_id``.

        Raises
        ------
        NotFoundError
            If no such entity exists.
        """

    @abstractmethod
    def list(self, specification: BaseSpecification[TEntity] | None = None) -> Sequence[TEntity]:
        """Return all stored entities, optionally filtered by ``specification``."""

    def __contains__(self, entity_id: TId) -> bool:
        return self.find(entity_id).is_some


class InMemoryRepository(BaseRepository[TEntity, TId]):
    """A dictionary-backed :class:`BaseRepository`, suitable for unit tests,
    examples, and prototypes -- not for production use.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> @dataclass(frozen=True, slots=True, eq=False)
    ... class Item(BaseEntity[str]):
    ...     name: str
    >>> repo: InMemoryRepository[Item, str] = InMemoryRepository()
    >>> repo.add(Item(id="1", name="widget"))
    >>> repo.get("1").name
    'widget'
    >>> "1" in repo
    True
    """

    def __init__(self) -> None:
        self._storage: dict[TId, TEntity] = {}

    def add(self, entity: TEntity) -> None:
        entity_id: TId = entity.id
        if entity_id in self._storage:
            raise DuplicateError(f"Entity with id {entity_id!r} already exists.")
        self._storage[entity_id] = entity

    def get(self, entity_id: TId) -> TEntity:
        try:
            return self._storage[entity_id]
        except KeyError as exc:
            raise NotFoundError(f"No entity found with id {entity_id!r}.") from exc

    def find(self, entity_id: TId) -> Maybe[TEntity]:
        entity = self._storage.get(entity_id)
        return Maybe.nothing() if entity is None else Maybe.some(entity)

    def remove(self, entity_id: TId) -> None:
        try:
            del self._storage[entity_id]
        except KeyError as exc:
            raise NotFoundError(f"No entity found with id {entity_id!r}.") from exc

    def list(self, specification: BaseSpecification[TEntity] | None = None) -> Sequence[TEntity]:
        values = list(self._storage.values())
        if specification is None:
            return values
        return [value for value in values if specification.is_satisfied_by(value)]
