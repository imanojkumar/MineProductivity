"""``registered_in``: the generic ``@register`` decorator factory for
straightforward key-based registration (design spec §17).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from mineproductivity.core import BaseMetadata

from mineproductivity.registry.registry import Registry, TKey

__all__ = ["registered_in"]

TItem = TypeVar("TItem")


def registered_in(
    registry: Registry[TKey, TItem],
    *,
    key_of: Callable[[TItem], TKey],
    metadata_of: Callable[[TItem], BaseMetadata] | None = None,
) -> Callable[[TItem], TItem]:
    """Build a decorator that registers the decorated item into
    ``registry``, deriving its key (and, optionally, its metadata) from
    the item itself.

    Suitable whenever registration needs nothing beyond "derive a key,
    reject a duplicate" -- ``mineproductivity.connectors.register_connector``
    is exactly this, a thin, partially-applied wrapper around
    ``registered_in()``. A domain package that needs additional
    registration-time validation implements its own ``@register``
    instead, calling ``Registry.register()`` directly:
    ``mineproductivity.kpis.register`` does this to also raise
    ``KPICircularDependencyError`` at registration time (never deferred
    to first use). ``mineproductivity.ontology.register_equipment`` is
    unrelated to this mechanism entirely -- ``ontology`` sits below
    ``registry`` in the dependency stack (``core -> ontology -> events ->
    registry``) and cannot import it; its entity-type registry is a
    separate, internal mechanism. "One discovery pattern for the whole
    ecosystem" (Cookbook Part I, Ch. 9) means every domain package builds
    its ``@register`` the same *shape* -- decorator + typed registry +
    raising lookup -- not that every one is literally built from this
    one function.

    Examples
    --------
    >>> REGISTRY: Registry[str, type] = Registry(name="kpis")
    >>> register = registered_in(REGISTRY, key_of=lambda cls: cls.__name__)
    >>> @register
    ... class FuelPerTonne: pass
    >>> REGISTRY.get("FuelPerTonne") is FuelPerTonne
    True
    """

    def decorator(item: TItem) -> TItem:
        key = key_of(item)
        metadata = metadata_of(item) if metadata_of is not None else None
        registry.register(key, item, metadata=metadata)
        return item

    return decorator
