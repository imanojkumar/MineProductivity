"""``DashboardBuilder``: fluent, step-by-step ``Dashboard``
construction (design spec §12) -- the first concrete subclass of
``core.BaseBuilder`` anywhere in this series (§3.4): dashboard
construction has enough optional steps (add a widget, set a layout,
choose a theme) that ``BaseBuilder``'s own "prefer over a
constructor... when construction has many optional steps" guidance
applies directly. ``build_result()`` is the inherited, unoverridden
``core.BaseBuilder.build_result()`` -- no second non-raising variant
is introduced.

Disclosed reference resolution of spec-level imprecision: the §12
builder surface names no id-choosing step, so ``build()`` assigns a
fresh ``"DASH-"``-prefixed identity per built instance --
``Dashboard.id``, not ``name``, is what ``DashboardRepository`` keys
on (§23).
"""

from __future__ import annotations

import uuid
from typing import Self

from mineproductivity.core import BaseBuilder

from mineproductivity.visualization.dashboard import Dashboard
from mineproductivity.visualization.exceptions import VisualizationValidationError
from mineproductivity.visualization.layout import Layout
from mineproductivity.visualization.widget import Widget

__all__ = ["DashboardBuilder"]


class DashboardBuilder(BaseBuilder[Dashboard]):
    """Accumulates widgets, layout, and theme choices, then produces a
    ``Dashboard`` via :meth:`build` (design spec §12).

    Examples
    --------
    >>> dashboard = (
    ...     DashboardBuilder(owner="supervisor-a")
    ...     .with_name("Night Shift Handover")
    ...     .with_theme("DARK_HIGH_CONTRAST")
    ...     .build()
    ... )
    >>> dashboard.name
    'Night Shift Handover'
    """

    def __init__(self, *, owner: str) -> None:
        self._owner = owner
        self._name = ""
        self._widgets: list[Widget] = []
        self._layout: Layout | None = None
        self._theme_code = ""

    def with_name(self, name: str) -> Self:
        self._name = name
        return self

    def with_widget(self, widget: Widget) -> Self:
        self._widgets.append(widget)
        return self

    def with_layout(self, layout: Layout) -> Self:
        self._layout = layout
        return self

    def with_theme(self, theme_code: str) -> Self:
        self._theme_code = theme_code
        return self

    def reset(self) -> Self:
        """Clear every accumulated step (``owner`` is kept -- it is
        the builder's construction-time identity, not an accumulated
        step), per ``core.BaseBuilder.reset()``'s own contract."""
        self._name = ""
        self._widgets = []
        self._layout = None
        self._theme_code = ""
        return self

    def build(self) -> Dashboard:
        """Construct the final ``Dashboard``.

        Raises
        ------
        VisualizationValidationError
            For an empty ``name`` or ``owner`` (design spec §12) --
            the incomplete-state failure ``core.BaseBuilder.build()``'s
            own docstring anticipates.
        """
        if not self._name.strip():
            raise VisualizationValidationError(
                "DashboardBuilder.build() requires with_name() with a non-empty name"
            )
        if not self._owner.strip():
            raise VisualizationValidationError(
                "DashboardBuilder.build() requires a non-empty owner"
            )
        return Dashboard(
            id=f"DASH-{uuid.uuid4().hex[:12]}",
            name=self._name,
            owner=self._owner,
            widgets=tuple(self._widgets),
            layout=self._layout,
            theme_code=self._theme_code,
        )
