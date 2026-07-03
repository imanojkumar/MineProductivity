"""``registered_in``: the generic ``@register`` decorator factory every
domain package's own ``@register`` decorator is built from (design spec
§17).
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

    This is the single mechanism every domain package's own ``@register``
    decorator (``kpis.register``, ``connectors.register``,
    ``ontology.register_equipment``, ...) is a thin, partially-applied
    wrapper around -- so "one discovery pattern for the whole ecosystem"
    (Cookbook Part I, Ch. 9) holds at the decorator level too, not just
    the registry level.

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
