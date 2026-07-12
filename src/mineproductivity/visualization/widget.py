"""``Widget``: one bound, placed unit of presentation on a
``Dashboard`` (design spec §10) -- references a registered
``Visualization`` type by code and names the evidence it binds to via
an open, renderer-interpreted mapping.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType

from mineproductivity.core import BaseValueObject

from mineproductivity.visualization.exceptions import VisualizationValidationError

__all__ = ["Widget"]


@dataclasses.dataclass(frozen=True, slots=True)
class Widget(BaseValueObject):
    """One bound unit of presentation. ``binding`` is an open
    ``Mapping[str, str]`` naming which evidence this widget reads
    (e.g. ``{"kpi_code": "PROD.TPH", "scope": "site=Karara"}``) --
    never a typed reference (design spec §10), and never interpreted
    by this package's own code on a ``Renderer``'s behalf (§16).

    Examples
    --------
    >>> Widget(
    ...     code="tph_card", visualization_code="KPI_CARD.Standard",
    ...     binding={"kpi_code": "PROD.TPH"},
    ... ).binding["kpi_code"]
    'PROD.TPH'
    """

    code: str
    visualization_code: str
    binding: Mapping[str, str] = dataclasses.field(default_factory=dict, kw_only=True)

    def _normalize(self) -> None:
        super(Widget, self)._normalize()
        object.__setattr__(self, "binding", MappingProxyType(dict(self.binding)))

    def validate(self) -> None:
        if not self.code.strip():
            raise VisualizationValidationError("Widget.code must not be empty")
        if not self.visualization_code.strip():
            raise VisualizationValidationError("Widget.visualization_code must not be empty")
