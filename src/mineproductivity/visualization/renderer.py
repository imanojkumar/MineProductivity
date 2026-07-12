"""``Renderer``/``RendererMetadata``/``RenderedOutput``:
interface-only extension point for converting a ``PresentationModel``
into a concrete medium (design spec §16) -- no concrete implementation
ships in this package.

``Renderer`` is registered separately from ``Visualization``
(``RENDERERS``, not ``REGISTRY``, §20): a ``Visualization`` decides
*what* to show; a ``Renderer`` decides *how* to actually draw it in
one concrete medium. A concrete ``Renderer`` interprets
``Layout.slots``/``Widget.binding`` entirely on its own -- strictly as
data, never as executable code or a dynamic template (§31) -- and any
memoization of an expensive conversion step (e.g. document
generation) is that ``Renderer``'s own implementation detail, never a
shared package-level cache abstraction (§24).
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from mineproductivity.core import BaseMetadata, BaseValueObject

from mineproductivity.visualization.abstractions import VisualizationContext
from mineproductivity.visualization.exceptions import VisualizationValidationError
from mineproductivity.visualization.presentation import PresentationModel

__all__ = ["RenderedOutput", "Renderer", "RendererMetadata"]


@dataclasses.dataclass(frozen=True, slots=True)
class RendererMetadata(BaseMetadata):
    """The minimal registration schema for a discoverable ``Renderer``
    type -- as light as ``agents.ToolMetadata`` (spec 11 §17).

    Examples
    --------
    >>> meta = RendererMetadata(code="HTML.Standard", description="Renders to HTML.")
    >>> meta.name
    'HTML.Standard'
    """

    name: str = dataclasses.field(default="", kw_only=True)
    code: str
    description: str = dataclasses.field(kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)

    def _normalize(self) -> None:
        super(RendererMetadata, self)._normalize()
        if not self.name:
            object.__setattr__(self, "name", self.code)

    def validate(self) -> None:
        if not self.code.strip():
            raise VisualizationValidationError("RendererMetadata.code must not be empty")
        super(RendererMetadata, self).validate()


class Renderer(ABC):
    """The contract a future rendering-backend plugin implements (an
    HTML renderer, a PDF renderer, a terminal renderer). THIS MODULE
    SHIPS NO CONCRETE SUBCLASS -- choosing a specific charting or
    document-generation library is exactly the kind of implementation
    decision this package's charter (design spec §3.1, §3.5, §4)
    excludes."""

    meta: ClassVar[RendererMetadata]

    @abstractmethod
    def render(self, model: PresentationModel, *, context: VisualizationContext) -> RenderedOutput:
        """Convert ``model`` into this renderer's concrete medium. A
        legitimately incomplete model surfaces as a warning-carrying
        ``RenderedOutput``, never a raise (design spec §30)."""


@dataclasses.dataclass(frozen=True, slots=True)
class RenderedOutput(BaseValueObject):
    """A record of one ``Renderer.render()`` call and its result
    (design spec §16).

    Examples
    --------
    >>> RenderedOutput(format="html", payload="<div>1212.1</div>").format
    'html'
    """

    format: str
    payload: Any
    warnings: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
