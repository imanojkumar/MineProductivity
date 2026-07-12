"""``mineproductivity.visualization`` -- the presentation layer
(design spec 12): the final package in the platform's architecture,
built directly above ``agents``. Defines *what* is shown
(``Visualization``/``PresentationModel``), *where* it lives
(``Widget``/``Dashboard``/``Layout``/``Theme``), and *how* rendering
is orchestrated (``RenderingPipeline``/``Report``/``Export``) --
``Visualization`` and ``Renderer`` are interface-only extension
points; choosing a charting, templating, or document-generation
backend is exactly the implementation decision this package excludes
(§3.1, §4).

Public API (design spec §7) -- every name stable once implementation
begins.
"""

from __future__ import annotations

from mineproductivity.visualization._registry import (
    REGISTRY,
    RENDERERS,
    register,
    register_renderer,
)
from mineproductivity.visualization.abstractions import (
    Visualization,
    VisualizationCategory,
    VisualizationContext,
    VisualizationMetadata,
)
from mineproductivity.visualization.dashboard import Dashboard
from mineproductivity.visualization.dashboard_builder import DashboardBuilder
from mineproductivity.visualization.discovery import by_owner, by_theme
from mineproductivity.visualization.exceptions import (
    DashboardNotFoundError,
    RenderingError,
    VisualizationValidationError,
    VisualizationVersionConflictError,
)
from mineproductivity.visualization.export import ExportRequest, ExportResult
from mineproductivity.visualization.layout import Layout
from mineproductivity.visualization.persistence import DashboardRepository
from mineproductivity.visualization.pipeline import RenderingPipeline
from mineproductivity.visualization.presentation import PresentationModel
from mineproductivity.visualization.renderer import (
    RenderedOutput,
    Renderer,
    RendererMetadata,
)
from mineproductivity.visualization.report import Report
from mineproductivity.visualization.report_builder import ReportBuilder
from mineproductivity.visualization.theme import Theme
from mineproductivity.visualization.widget import Widget

__all__ = [
    "Dashboard",
    "DashboardBuilder",
    "DashboardNotFoundError",
    "DashboardRepository",
    "ExportRequest",
    "ExportResult",
    "Layout",
    "PresentationModel",
    "REGISTRY",
    "RENDERERS",
    "RenderedOutput",
    "Renderer",
    "RendererMetadata",
    "RenderingError",
    "RenderingPipeline",
    "Report",
    "ReportBuilder",
    "Theme",
    "Visualization",
    "VisualizationCategory",
    "VisualizationContext",
    "VisualizationMetadata",
    "VisualizationValidationError",
    "VisualizationVersionConflictError",
    "Widget",
    "by_owner",
    "by_theme",
    "register",
    "register_renderer",
]
