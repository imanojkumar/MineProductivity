"""``Theme``: shared visual styling (design spec §21) -- plain,
non-polymorphic configuration data referenced by a ``Dashboard`` via
``theme_code``, deliberately NOT registrable: a theme carries no
behavior to dispatch to, unlike a ``Visualization`` or a ``Renderer``
(§21, §32's recorded anti-pattern against a third ``Registry``).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType

from mineproductivity.core import BaseValueObject

from mineproductivity.visualization.exceptions import VisualizationValidationError

__all__ = ["Theme"]


@dataclasses.dataclass(frozen=True, slots=True)
class Theme(BaseValueObject):
    """A small, named visual styling configuration. ``palette``/
    ``typography`` are renderer-interpreted open mappings, never a
    typed per-property schema (design spec §21).

    Examples
    --------
    >>> Theme(code="DARK_HIGH_CONTRAST", palette={"background": "#000"}).code
    'DARK_HIGH_CONTRAST'
    """

    code: str
    palette: Mapping[str, str] = dataclasses.field(default_factory=dict, kw_only=True)
    typography: Mapping[str, str] = dataclasses.field(default_factory=dict, kw_only=True)

    def _normalize(self) -> None:
        super(Theme, self)._normalize()
        object.__setattr__(self, "palette", MappingProxyType(dict(self.palette)))
        object.__setattr__(self, "typography", MappingProxyType(dict(self.typography)))

    def validate(self) -> None:
        if not self.code.strip():
            raise VisualizationValidationError("Theme.code must not be empty")
