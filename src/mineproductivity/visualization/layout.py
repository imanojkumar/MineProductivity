"""``Layout``: widget arrangement (design spec §10) -- maps each
``Widget.code`` to an opaque, renderer-interpreted position spec.
This package never parses ``slots``: the same 'never executes, only
stores' posture ``optimization.Constraint.expression`` (spec 10 §9)
and ``agents.AgentPolicy.rule`` (spec 11 §10) already establish,
applied here to layout geometry.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType

from mineproductivity.core import BaseValueObject

from mineproductivity.visualization.exceptions import VisualizationValidationError

__all__ = ["Layout"]


@dataclasses.dataclass(frozen=True, slots=True)
class Layout(BaseValueObject):
    """Maps each ``Widget.code`` to an opaque position spec (a CSS
    grid area, a terminal row/column pair, a PDF page region) a
    concrete ``Renderer`` interprets entirely on its own (design spec
    §10, §16).

    Examples
    --------
    >>> Layout(code="handover_grid", slots={"tph_card": "row=1;col=1"}).slots["tph_card"]
    'row=1;col=1'
    """

    code: str
    slots: Mapping[str, str] = dataclasses.field(default_factory=dict, kw_only=True)

    def _normalize(self) -> None:
        super(Layout, self)._normalize()
        object.__setattr__(self, "slots", MappingProxyType(dict(self.slots)))

    def validate(self) -> None:
        if not self.slots:
            raise VisualizationValidationError("Layout.slots must not be empty")
