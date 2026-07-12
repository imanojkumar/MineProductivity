"""The ``mineproductivity.visualization`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

__all__ = [
    "DashboardNotFoundError",
    "RenderingError",
    "VisualizationValidationError",
    "VisualizationVersionConflictError",
]


class VisualizationValidationError(ValidationError):
    """A ``VisualizationMetadata``, ``Dashboard``, ``Widget``, or
    ``Layout`` failed validation (design spec §26, §10) -- e.g. an
    empty code, a Widget with no bound visualization_code, or a Layout
    with no slots."""


class DashboardNotFoundError(NotFoundError):
    """``DashboardRepository.get(dashboard_id)`` found no dashboard
    for that id, or ``REGISTRY.get(code)``/``RENDERERS.get(code)``
    found no registered type for that code (design spec §6)."""


class RenderingError(MineProductivityError):
    """``RenderingPipeline`` raised for a step that should have been
    structurally valid -- distinct from a legitimately-incomplete
    widget binding (design spec §30's 'qualify, don't coerce' rule),
    which returns a ``PresentationModel``/``RenderedOutput`` carrying
    a warning instead of raising."""


class VisualizationVersionConflictError(RegistrationError):
    """A plugin attempted to re-register an existing ``Visualization``
    or ``Renderer`` type code with materially different metadata
    without a version bump, mirroring
    ``agents.AgentVersionConflictError``'s identical reasoning
    (spec 11 §6)."""
