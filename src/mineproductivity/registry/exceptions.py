"""The ``mineproductivity.registry`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError

__all__ = [
    "DuplicateRegistrationError",
    "RegistrationError",
    "UnregisteredLookupError",
    "VersionIncompatibleError",
]


class RegistrationError(MineProductivityError):
    """Base of registry-specific errors."""


class DuplicateRegistrationError(RegistrationError):
    """``Registry.register()`` called with a key that already exists.

    Registration is add-only (design spec AD-RG-04) -- re-registering an
    existing key is always rejected, never silently accepted as an
    update.
    """


class UnregisteredLookupError(NotFoundError):
    """``Registry.get()`` found no item for the given key."""


class VersionIncompatibleError(RegistrationError):
    """A plugin's declared ``core_version_range`` excludes the installed
    core version."""
