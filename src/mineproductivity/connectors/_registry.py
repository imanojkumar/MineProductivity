"""The connector registry -- a typed specialization of the generic
Registry Framework mechanism (design spec §17), factored into its own
internal module so ``connectors/__init__.py`` can register the built-in
reference connectors without a circular import (each connector module
needs ``register_connector`` too, for a third-party plugin author's
``@register_connector`` usage per the public API).
"""

from __future__ import annotations

from mineproductivity.registry import Registry, registered_in

from mineproductivity.connectors.base import FMSConnector

__all__ = ["CONNECTORS", "get_connector", "register_connector"]

CONNECTORS: Registry[str, type[FMSConnector]] = Registry(name="connectors")

register_connector = registered_in(CONNECTORS, key_of=lambda cls: cls.name)


def get_connector(name: str) -> type[FMSConnector]:
    """Raising lookup of a registered connector class by its ``name``.

    Raises
    ------
    UnregisteredLookupError
        If no connector is registered under ``name``.
    """
    return CONNECTORS.get(name)
