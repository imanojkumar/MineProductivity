"""``KPIIdentifier``/``parse_identifier``: the ``NAMESPACE.Name`` KPI
naming standard (Developer & Cookbook Guide Part III, "The KPI Naming
Standard").
"""

from __future__ import annotations

import dataclasses

from mineproductivity.core import BaseValueObject

from mineproductivity.kpis.exceptions import KPIValidationError

__all__ = ["KPIIdentifier", "parse_identifier"]

#: The controlled namespace list (design spec §20): the eight namespaces
#: named in the KPI Engine spec's own scope (§2) plus Appendix A's
#: extension namespaces.
CONTROLLED_NAMESPACES = frozenset(
    {
        "PROD",
        "UTIL",
        "MAINT",
        "HAUL",
        "DISP",
        "QUAL",
        "COST",
        "ENERGY",
        "CARBON",
        "WATER",
        "SAFE",
        "AUTO",
        "GRADE",
        "BLEND",
        "CRUSH",
        "PROC",
        "STOCK",
        "RAIL",
        "PORT",
        "TWIN",
        "DI",
        "AI",
    }
)


@dataclasses.dataclass(frozen=True, slots=True)
class KPIIdentifier(BaseValueObject):
    """A parsed ``NAMESPACE.Name[.Specialization...]`` KPI code.

    Examples
    --------
    >>> identifier = parse_identifier("PROD.TPH.Ore")
    >>> identifier.namespace, identifier.name, identifier.specialization
    ('PROD', 'TPH', ('Ore',))
    >>> str(identifier)
    'PROD.TPH.Ore'
    """

    namespace: str
    name: str
    specialization: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)

    def __str__(self) -> str:
        return ".".join((self.namespace, self.name, *self.specialization))


def parse_identifier(code: str) -> KPIIdentifier:
    """Parse and validate ``code`` against the ``NAMESPACE.Name`` naming
    standard: a controlled uppercase namespace, a PascalCase name, and
    zero or more PascalCase dotted specializations (``PROD.TPH.Ore``).

    Raises
    ------
    KPIValidationError
        If ``code`` does not conform.
    """
    parts = code.split(".")
    if len(parts) < 2:
        raise KPIValidationError(f"{code!r} is not a valid NAMESPACE.Name KPI identifier")

    namespace, name, *specialization = parts
    if namespace not in CONTROLLED_NAMESPACES:
        raise KPIValidationError(
            f"{namespace!r} is not a recognized KPI namespace (controlled list: "
            f"{sorted(CONTROLLED_NAMESPACES)})"
        )
    _require_pascal_case(name, code=code)
    for piece in specialization:
        _require_pascal_case(piece, code=code)

    return KPIIdentifier(namespace=namespace, name=name, specialization=tuple(specialization))


def _require_pascal_case(piece: str, *, code: str) -> None:
    if not piece or not piece[0].isupper() or not piece.isalnum():
        raise KPIValidationError(f"{code!r}: {piece!r} must be a non-empty PascalCase segment")
