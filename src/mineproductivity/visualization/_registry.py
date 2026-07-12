"""The Visualization Registry and the Renderer Registry (design spec
§20) -- two typed specializations of ``registry.Registry``, following
``agents._registry``'s two-registry precedent (spec 11 §22) exactly,
since a ``Visualization`` type and a ``Renderer`` type are orthogonal
registrable concepts: what can be shown, versus how it is drawn. The
two are never merged. Both answer the type-level question ("which
types are known"), never conflated with ``DashboardRepository``
(instance-level) or ``discovery.py`` (query facade). Entry-point
discovery uses ``registry.EntryPointDiscovery`` with
``EntryPointSpec(group="mineproductivity.visualization",
target_registry="visualization")`` and
``EntryPointSpec(group="mineproductivity.visualization.renderers",
target_registry="visualization.renderers")`` (design spec §28).
"""

from __future__ import annotations

from mineproductivity.registry import Registry

from mineproductivity.visualization.abstractions import Visualization
from mineproductivity.visualization.exceptions import (
    VisualizationValidationError,
    VisualizationVersionConflictError,
)
from mineproductivity.visualization.renderer import Renderer

__all__ = ["REGISTRY", "RENDERERS", "register", "register_renderer"]

REGISTRY: Registry[str, type[Visualization]] = Registry(name="visualization")
RENDERERS: Registry[str, type[Renderer]] = Registry(name="visualization.renderers")


def register(cls: type[Visualization]) -> type[Visualization]:
    """Register ``cls`` into :data:`REGISTRY`, keyed by
    ``cls.meta.code``.

    Raises
    ------
    VisualizationValidationError
        If ``cls.meta.code`` is empty (defensive, redundant guard --
        ``VisualizationMetadata.validate()`` already rejects it).
    VisualizationVersionConflictError
        If ``cls.meta.code`` is already registered -- add-only, raised
        at registration time, never deferred (design spec §23).
    """
    if not cls.meta.code:
        raise VisualizationValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = REGISTRY.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise VisualizationVersionConflictError(
            f"Visualization code {cls.meta.code!r} is already registered; changing what "
            f"it means requires a new code or a reviewed version bump, not "
            f"re-registration"
        )

    return cls


def register_renderer(cls: type[Renderer]) -> type[Renderer]:
    """Register ``cls`` into :data:`RENDERERS`, keyed by
    ``cls.meta.code`` -- identical shape and identical error semantics
    as :func:`register`, specialized for ``Renderer`` (design spec
    §20).

    Raises
    ------
    VisualizationValidationError
        If ``cls.meta.code`` is empty.
    VisualizationVersionConflictError
        If ``cls.meta.code`` is already registered in
        :data:`RENDERERS`.
    """
    if not cls.meta.code:
        raise VisualizationValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = RENDERERS.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise VisualizationVersionConflictError(
            f"Renderer code {cls.meta.code!r} is already registered; changing what it "
            f"means requires a new code or a reviewed version bump, not "
            f"re-registration"
        )

    return cls
