"""The Agent Registry and the Tool Registry (design spec §22) -- two
typed specializations of ``registry.Registry``, the first package in
this series to hold two distinct ``Registry`` instances rather than
one, since an ``Agent`` type and a ``Tool`` type are orthogonal
registrable concepts (§22): an ``Agent`` decides; a ``Tool`` acts at
an ``Agent``'s direction. The two are never merged. Both answer the
type-level question ("which types are known"), never conflated with
``TaskRepository`` (instance-level) or ``discovery.py`` (query
facade). Entry-point discovery uses ``registry.EntryPointDiscovery``
with ``EntryPointSpec(group="mineproductivity.agents",
target_registry="agents")`` and
``EntryPointSpec(group="mineproductivity.agents.tools",
target_registry="agents.tools")`` (design spec §31), exactly as every
prior domain package already wires its own group.
"""

from __future__ import annotations

from mineproductivity.registry import Registry

from mineproductivity.agents.abstractions import Agent
from mineproductivity.agents.exceptions import (
    AgentValidationError,
    AgentVersionConflictError,
)
from mineproductivity.agents.tool import Tool

__all__ = ["REGISTRY", "TOOLS", "register", "register_tool"]

REGISTRY: Registry[str, type[Agent]] = Registry(name="agents")
TOOLS: Registry[str, type[Tool]] = Registry(name="agents.tools")


def register(cls: type[Agent]) -> type[Agent]:
    """Register ``cls`` into :data:`REGISTRY`, keyed by
    ``cls.meta.code``.

    Raises
    ------
    AgentValidationError
        If ``cls.meta.code`` is empty (defensive, redundant guard --
        ``AgentMetadata.validate()`` already rejects it).
    AgentVersionConflictError
        If ``cls.meta.code`` is already registered -- add-only, raised
        at registration time, never deferred (design spec §26).
    """
    if not cls.meta.code:
        raise AgentValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = REGISTRY.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise AgentVersionConflictError(
            f"Agent code {cls.meta.code!r} is already registered; changing what it "
            f"means requires a new code or a reviewed version bump, not "
            f"re-registration"
        )

    return cls


def register_tool(cls: type[Tool]) -> type[Tool]:
    """Register ``cls`` into :data:`TOOLS`, keyed by ``cls.meta.code``
    -- identical shape and identical error semantics as
    :func:`register`, specialized for ``Tool`` (design spec §22).

    Raises
    ------
    AgentValidationError
        If ``cls.meta.code`` is empty.
    AgentVersionConflictError
        If ``cls.meta.code`` is already registered in :data:`TOOLS`.
    """
    if not cls.meta.code:
        raise AgentValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = TOOLS.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise AgentVersionConflictError(
            f"Tool code {cls.meta.code!r} is already registered; changing what it "
            f"means requires a new code or a reviewed version bump, not "
            f"re-registration"
        )

    return cls
