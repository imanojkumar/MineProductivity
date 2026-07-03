"""``VersionRange``/``VersionCompatibility``: gatekeeping a plugin against
the installed core version it declares support for.
"""

from __future__ import annotations

import dataclasses

from mineproductivity.core import BaseValueObject, ValidationError

from mineproductivity.registry.exceptions import VersionIncompatibleError

__all__ = ["VersionCompatibility", "VersionRange"]


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse a dotted numeric version string (``"1.2.3"``) into a tuple of
    ints for comparison. Only the leading digits of each dot-separated
    component are considered, so a pre-release suffix like ``"1.0.0rc1"``
    compares as ``(1, 0, 0)`` -- a minimal, dependency-free comparator;
    exact pre-release ordering is out of scope for this package (no
    third-party version-parsing library is a dependency of the base
    install)."""
    parts: list[int] = []
    for component in version.split("."):
        digits = ""
        for char in component:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


@dataclasses.dataclass(frozen=True, slots=True)
class VersionRange(BaseValueObject):
    """A half-open version range: ``[min_version, max_version_exclusive)``,
    e.g. ``mineproductivity>=1.0,<2.0`` (Cookbook Part I, Ch. 9)."""

    min_version: str
    max_version_exclusive: str

    def validate(self) -> None:
        if not self.min_version.strip():
            raise ValidationError("VersionRange.min_version must not be empty")
        if not self.max_version_exclusive.strip():
            raise ValidationError("VersionRange.max_version_exclusive must not be empty")
        if _parse_version(self.min_version) >= _parse_version(self.max_version_exclusive):
            raise ValidationError("VersionRange.min_version must be < max_version_exclusive")


class VersionCompatibility:
    """Stateless version-range compatibility checks."""

    @staticmethod
    def is_compatible(plugin_range: VersionRange, core_version: str) -> bool:
        """Whether ``core_version`` falls within ``plugin_range``'s
        half-open ``[min_version, max_version_exclusive)`` range."""
        parsed = _parse_version(core_version)
        return (
            _parse_version(plugin_range.min_version)
            <= parsed
            < _parse_version(plugin_range.max_version_exclusive)
        )

    @staticmethod
    def check_or_raise(plugin_range: VersionRange, core_version: str) -> None:
        """Raise :class:`~mineproductivity.registry.exceptions.VersionIncompatibleError`
        if ``core_version`` falls outside ``plugin_range``."""
        if not VersionCompatibility.is_compatible(plugin_range, core_version):
            raise VersionIncompatibleError(
                f"installed core version {core_version!r} is not within the plugin's "
                f"declared range [{plugin_range.min_version}, {plugin_range.max_version_exclusive})"
            )
