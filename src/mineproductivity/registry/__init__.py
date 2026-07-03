"""``mineproductivity.registry`` -- the plugin-first backbone of
MineProductivity: the single, generic discovery-and-lookup mechanism
that lets KPIs, connectors, ontology entity types, and analytics models
be added to the platform as separate, installable packages, with zero
change to the core.

Implements ``docs/architecture/03_Registry_Framework_Design_Specification.md``
exactly. ``registry`` depends only on ``core`` -- see ``README.md`` for
the full set of architectural rules this package must satisfy.

Everything documented here is part of the public API and can be imported
directly from ``mineproductivity.registry``, e.g.::

    from mineproductivity.registry import Registry, EntryPointDiscovery
"""

from __future__ import annotations

from mineproductivity.registry.caching import DiscoveryCache
from mineproductivity.registry.decorators import registered_in
from mineproductivity.registry.entry_point import EntryPointDiscovery, EntryPointSpec
from mineproductivity.registry.exceptions import (
    DuplicateRegistrationError,
    RegistrationError,
    UnregisteredLookupError,
    VersionIncompatibleError,
)
from mineproductivity.registry.registry import Registry
from mineproductivity.registry.version_compat import VersionCompatibility, VersionRange

__all__ = [
    "DiscoveryCache",
    "DuplicateRegistrationError",
    "EntryPointDiscovery",
    "EntryPointSpec",
    "RegistrationError",
    "Registry",
    "UnregisteredLookupError",
    "VersionCompatibility",
    "VersionIncompatibleError",
    "VersionRange",
    "registered_in",
]
