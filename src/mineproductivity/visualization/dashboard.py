"""``Dashboard``: the persistent, editable presentation-configuration
entity (design spec §10).

Reuse audit: ``core.BaseEntity[str]`` reused by literal inheritance,
following ``agents.Task``'s precedent (spec 11 §11) -- identity-based
equality inherited unchanged; every change is a new instance via
``dataclasses.replace``, never in-place mutation. Deliberately carries
**no** ``status`` field and **no** ``with_state()`` method -- a
documented departure from ``Twin``/``SimulationRun``/
``OptimizationRun``/``Task``'s own precedent (§10, §3.3): a Dashboard
is a configuration a user edits, not a process that runs to
completion, so there is no lifecycle to track (§32's recorded
anti-pattern against imitating one mechanically).
"""

from __future__ import annotations

import dataclasses

from mineproductivity.core import BaseEntity

from mineproductivity.visualization.exceptions import VisualizationValidationError
from mineproductivity.visualization.layout import Layout
from mineproductivity.visualization.widget import Widget

__all__ = ["Dashboard"]


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Dashboard(BaseEntity[str]):
    """The root of one saved, editable presentation configuration --
    'Dashboard-as-entity' (design spec §10). Immutable; trivially safe
    to read and share across threads (§29). Two dashboards sharing
    the same ``name`` under different ``owner``\\ s are never in
    conflict -- ``id``, not ``name``, is the identity
    ``DashboardRepository`` keys on (§23).

    Examples
    --------
    >>> dashboard = Dashboard(id="DASH-1", name="Night Shift Handover", owner="supervisor-a")
    >>> dashboard.widgets
    ()
    >>> import dataclasses as dc
    >>> dc.replace(dashboard, theme_code="DARK_HIGH_CONTRAST").theme_code
    'DARK_HIGH_CONTRAST'
    >>> dashboard.theme_code  # the original instance is untouched
    ''
    """

    name: str
    owner: str
    widgets: tuple[Widget, ...] = dataclasses.field(default=(), kw_only=True)
    layout: Layout | None = dataclasses.field(default=None, kw_only=True)
    theme_code: str = dataclasses.field(default="", kw_only=True)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Design spec §25: non-empty ``name`` and ``owner``."""
        if not self.name.strip():
            raise VisualizationValidationError("Dashboard.name must not be empty")
        if not self.owner.strip():
            raise VisualizationValidationError("Dashboard.owner must not be empty")
