"""The canonical, six-category delay taxonomy.

Minimum shared contract published ahead of the full Ontology Framework
(scheduled for its own milestone; see
``docs/architecture/02_Ontology_Framework_Design_Specification.md`` and
Documentation Governance Rule #005). Nothing else from the Ontology
Framework -- no entity types, no registry, no relationships, no
reasoning -- is implemented here. ``mineproductivity.events`` imports
only ``DelayCategory`` from this module.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["DelayCategory"]


class DelayCategory(Enum):
    """The six mutually-exclusive, collectively-exhaustive delay
    categories, ruled canonical in Developer & Cookbook Guide Part III,
    "Canonical Semantics". Owned here as ontology reference data;
    consumed by ``events.DelayEvent`` and every ``UTIL``/``DELAY`` KPI.
    """

    SCHEDULED = "Scheduled"
    OPERATIONAL = "Operational"
    EQUIPMENT = "Equipment"
    PROCESS = "Process"
    EXTERNAL = "External"
    STANDBY = "Standby"

    @property
    def precedence(self) -> int:
        """Lower number wins when a delay could plausibly belong to more
        than one category (e.g. refuelling during a breakdown)."""
        return _PRECEDENCE[self]


_PRECEDENCE: dict[DelayCategory, int] = {
    DelayCategory.EQUIPMENT: 0,
    DelayCategory.OPERATIONAL: 1,
    DelayCategory.STANDBY: 2,
    DelayCategory.PROCESS: 3,
    DelayCategory.SCHEDULED: 4,
    DelayCategory.EXTERNAL: 5,
}
