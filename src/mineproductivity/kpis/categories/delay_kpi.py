"""``DelayKPI``: the ``DISP`` namespace.

Design spec §10.4 describes this category as "DELAY/DISP namespace: delay
hours by category, dispatch metrics," but §20's controlled namespace
list (the one ``parse_identifier``/``enforce_namespace`` actually
validates against) contains only ``DISP``, not ``DELAY`` -- the
governing, normative list for identifier validation. ``DelayKPI`` codes
therefore use the ``DISP`` namespace (e.g. ``DISP.DelayHoursByCategory``);
the class still reads ``events.DelayEvent``/``ontology.DelayCategory``
data, which is where the "delay" in the category's description comes
from.
"""

from __future__ import annotations

from abc import ABC

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace

__all__ = ["DelayKPI"]


class DelayKPI(BaseKPI, ABC):
    """``DISP`` namespace: delay hours by category, dispatch metrics,
    consuming :class:`~mineproductivity.ontology.DelayCategory`'s
    six-value taxonomy."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        enforce_namespace(cls, "DISP")
