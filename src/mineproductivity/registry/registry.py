"""``Registry[TKey, TItem]``: the one generic, type-safe registration
mechanism every domain package specializes rather than reimplements.
"""

from __future__ import annotations

import logging
from collections.abc import Hashable, Iterator, Sequence
from typing import Generic, TypeVar

from mineproductivity.core import BaseMetadata, BaseSpecification, Maybe, Result

from mineproductivity.registry.exceptions import DuplicateRegistrationError, UnregisteredLookupError

__all__ = ["Registry"]

_logger = logging.getLogger(__name__)

TKey = TypeVar("TKey", bound=Hashable)
TItem = TypeVar("TItem")


class Registry(Generic[TKey, TItem]):
    """A generic, type-safe, metadata-aware registration container.

    Every domain-specific registry (``KPIRegistry``, ``ConnectorRegistry``,
    ``EntityTypeRegistry``, ``AnalyticsRegistry``) is a type alias over
    this class, not a subclass with new behavior -- composition over
    inheritance, and one implementation to trust platform-wide (design
    spec AD-RG-01).

    A deliberate structural echo of
    :class:`~mineproductivity.core.repository.BaseRepository`: a registry
    *is*, conceptually, a repository whose entities are types/classes/
    callables instead of domain entities. ``Registry`` does not subclass
    ``BaseRepository``, since its keys are typically strings/codes rather
    than ``BaseEntity`` ids.

    Examples
    --------
    >>> registry: Registry[str, type] = Registry(name="widgets")
    >>> class Widget: pass
    >>> registry.register("widget", Widget).is_ok
    True
    >>> registry.get("widget") is Widget
    True
    >>> registry.register("widget", Widget).is_ok
    False
    """

    def __init__(self, *, name: str) -> None:
        self._name = name
        self._items: dict[TKey, TItem] = {}
        self._metadata: dict[TKey, BaseMetadata] = {}

    @property
    def name(self) -> str:
        """The domain-facing name this registry was constructed with
        (e.g. ``"kpis"``, ``"connectors"``) -- used in log messages and
        error details."""
        return self._name

    def register(
        self, key: TKey, item: TItem, *, metadata: BaseMetadata | None = None
    ) -> Result[None]:
        """Register ``item`` under ``key``.

        Registration is add-only (design spec §19, AD-RG-04): re-
        registering an existing key -- even with the exact same item --
        is always rejected, never silently accepted as an update.

        Returns
        -------
        Result[None]
            ``Result.ok(None)`` on success, or
            ``Result.err(DuplicateRegistrationError)`` if ``key`` is
            already registered.
        """
        existing = self._items.get(key)
        if existing is not None:
            _logger.warning(
                "registry %r: duplicate registration for key %r rejected "
                "(existing: %s, attempted: %s)",
                self._name,
                key,
                getattr(existing, "__module__", "<unknown>"),
                getattr(item, "__module__", "<unknown>"),
            )
            return Result.err(
                DuplicateRegistrationError(
                    f"registry {self._name!r}: key {key!r} is already registered"
                )
            )
        self._items[key] = item
        if metadata is not None:
            self._metadata[key] = metadata
        return Result.ok(None)

    def lookup(self, key: TKey) -> Maybe[TItem]:
        """Non-raising lookup of ``key``."""
        item = self._items.get(key)
        return Maybe.nothing() if item is None else Maybe.some(item)

    def get(self, key: TKey) -> TItem:
        """Raising lookup of ``key``.

        Raises
        ------
        UnregisteredLookupError
            If no item is registered under ``key``.
        """
        item = self._items.get(key)
        if item is None:
            raise UnregisteredLookupError(
                f"registry {self._name!r}: no item registered for key {key!r}"
            )
        return item

    def list(self, specification: BaseSpecification[TItem] | None = None) -> Sequence[TItem]:
        """All registered items, optionally filtered by ``specification`` --
        mirrors :meth:`~mineproductivity.core.repository.BaseRepository.list`'s
        shape deliberately."""
        values = list(self._items.values())
        if specification is None:
            return values
        return [value for value in values if specification.is_satisfied_by(value)]

    def metadata_for(self, key: TKey) -> Maybe[BaseMetadata]:
        """Non-raising lookup of the metadata attached to ``key`` at
        registration time, if any."""
        metadata = self._metadata.get(key)
        return Maybe.nothing() if metadata is None else Maybe.some(metadata)

    def __contains__(self, key: TKey) -> bool:
        return key in self._items

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[TKey]:
        return iter(self._items)
