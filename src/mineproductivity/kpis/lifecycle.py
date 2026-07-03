"""``KPIStatus``: the KPI type lifecycle, Developer & Cookbook Guide Part
III Introduction.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["KPIStatus"]


class KPIStatus(Enum):
    """``Proposed -> Active -> Deprecated -> Retired``. A ``Deprecated``
    KPI remains resolvable via ``meta.aliases``/``deprecated_successor``;
    a ``Retired`` identifier is never reused."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
