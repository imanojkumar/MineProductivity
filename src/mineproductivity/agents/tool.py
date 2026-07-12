"""``Tool``/``ToolMetadata``/``ToolInvocation``: interface-only
extension point for invokable external actions (design spec §17) --
no concrete implementation ships in this package.

Reuse audit: ``core.BaseMetadata``/``core.BaseValueObject`` and the
``MappingProxyType``-freezing convention reused verbatim. ``Tool`` is
registered separately from ``Agent`` (``TOOLS``, not ``REGISTRY``,
design spec §22): an ``Agent`` decides; a ``Tool`` acts on the world
(or queries it) at an ``Agent``'s direction. This package never
invokes a ``Tool`` on an ``Agent``'s behalf -- a concrete ``Agent``
implementation looks up a needed ``Tool`` by code via ``TOOLS.get()``,
invokes it, and carries the resulting ``ToolInvocation`` on its own
``AgentResult`` (§17, §20). A concrete ``Tool`` implementation
validates its own ``arguments`` independently -- permission-checking
authorizes *that* an action category may be attempted, not that every
argument value is safe (§33).
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Any, ClassVar

from mineproductivity.core import BaseMetadata, BaseValueObject

from mineproductivity.agents.abstractions import AgentContext
from mineproductivity.agents.exceptions import AgentValidationError

__all__ = ["Tool", "ToolInvocation", "ToolMetadata"]


@dataclasses.dataclass(frozen=True, slots=True)
class ToolMetadata(BaseMetadata):
    """The minimal registration schema for a discoverable ``Tool``
    type -- as light as ``optimization.OptimizationMetadata`` (design
    spec §17, §29).

    Examples
    --------
    >>> meta = ToolMetadata(code="TOOL.DispatchQuery", description="Queries dispatch.")
    >>> meta.name
    'TOOL.DispatchQuery'
    """

    name: str = dataclasses.field(default="", kw_only=True)
    code: str
    description: str = dataclasses.field(kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)

    def _normalize(self) -> None:
        super(ToolMetadata, self)._normalize()
        if not self.name:
            object.__setattr__(self, "name", self.code)

    def validate(self) -> None:
        if not self.code.strip():
            raise AgentValidationError("ToolMetadata.code must not be empty")
        super(ToolMetadata, self).validate()


class Tool(ABC):
    """The contract a future tool-integration plugin implements (a
    dispatch-system query, an ERP call, a specific external API).
    THIS MODULE SHIPS NO CONCRETE SUBCLASS -- choosing a specific
    external system's integration details is exactly the kind of
    implementation decision this package's charter (design spec §3.1,
    §3.5, §4) excludes."""

    meta: ClassVar[ToolMetadata]

    @abstractmethod
    def invoke(self, *, arguments: Mapping[str, Any], context: AgentContext) -> Mapping[str, Any]:
        """Perform this tool's action with ``arguments``, returning
        its structured result. Implementations validate ``arguments``
        independently (design spec §33)."""


@dataclasses.dataclass(frozen=True, slots=True)
class ToolInvocation(BaseValueObject):
    """A record of one ``Tool.invoke()`` call and its result, carried
    on the eventual ``AgentResult`` (design spec §20) for audit
    purposes.

    Examples
    --------
    >>> from datetime import timezone
    >>> invocation = ToolInvocation(
    ...     tool_code="TOOL.DispatchQuery", arguments={"pit": "north"},
    ...     result={"trucks": 12}, invoked_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    ... )
    >>> invocation.result["trucks"]
    12
    """

    tool_code: str
    arguments: Mapping[str, Any]
    result: Mapping[str, Any]
    invoked_at: datetime

    def _normalize(self) -> None:
        super(ToolInvocation, self)._normalize()
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
        object.__setattr__(self, "result", MappingProxyType(dict(self.result)))
