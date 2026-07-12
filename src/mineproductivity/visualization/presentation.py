"""``PresentationModel``: the structured, backend-independent output
of ``Visualization._render`` (design spec §9).

Reuse audit: ``core.BaseValueObject`` and the
``MappingProxyType``-freezing convention reused verbatim.
``evidence_refs`` continues ``decision.Explanation.evidence_refs``'s
"structured contract over prose" idiom (spec 07 §17), applied to a
presentation rather than a recommendation. Deliberately carries no
rendered bytes, HTML, or pixels of its own -- that is exactly the
``Renderer``'s (§16) responsibility, never this package's.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject

from mineproductivity.visualization.abstractions import VisualizationCategory

__all__ = ["PresentationModel"]


@dataclasses.dataclass(frozen=True, slots=True)
class PresentationModel(BaseValueObject):
    """What should be shown -- series, labels, category hint, evidence
    references -- without committing to any concrete medium (design
    spec §9). ``series`` is an open ``Mapping[str, Any]``, since one
    category's data shape (a Pareto front's two axes; a timeline's
    ordered events) varies far more than a lower package's own result
    shapes do.

    Examples
    --------
    >>> model = PresentationModel(
    ...     category=VisualizationCategory.KPI_CARD,
    ...     title="Tonnes per hour",
    ...     series={"value": 1212.1},
    ...     evidence_refs=("PROD.TPH",),
    ... )
    >>> model.series["value"]
    1212.1
    """

    category: VisualizationCategory
    title: str
    series: Mapping[str, Any] = dataclasses.field(default_factory=dict, kw_only=True)
    evidence_refs: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    warnings: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)

    def _normalize(self) -> None:
        super(PresentationModel, self)._normalize()
        object.__setattr__(self, "series", MappingProxyType(dict(self.series)))
