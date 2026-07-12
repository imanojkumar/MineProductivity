"""``ReportBuilder``: fluent, step-by-step ``Report`` construction
(design spec §14), composing ``RenderingPipeline`` (§11) once per
requested section rather than duplicating its dispatch logic -- the
same composition-over-duplication posture ``agents.WorkflowEngine``
establishes over ``agents.TaskExecutor`` (spec 11 §13).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self

from mineproductivity.core import BaseBuilder

from mineproductivity.visualization.abstractions import VisualizationContext
from mineproductivity.visualization.pipeline import RenderingPipeline
from mineproductivity.visualization.renderer import RenderedOutput
from mineproductivity.visualization.report import Report
from mineproductivity.visualization.widget import Widget

__all__ = ["ReportBuilder"]


class ReportBuilder(BaseBuilder[Report]):
    """Accumulates rendered sections -- each produced by an actual
    ``RenderingPipeline.render`` call, never a re-implementation of it
    -- then assembles the final ``Report`` via :meth:`build` (design
    spec §14). A section that produced a warning-carrying
    ``RenderedOutput`` has that warning preserved on the final
    ``Report.warnings``, never silently dropped (§30)."""

    def __init__(self, *, report_code: str, pipeline: RenderingPipeline) -> None:
        self._report_code = report_code
        self._pipeline = pipeline
        self._sections: list[RenderedOutput] = []

    def with_section(
        self, widget: Widget, *, context: VisualizationContext, renderer_code: str
    ) -> Self:
        """Render one section now, via the composed pipeline, and
        append it (design spec §14)."""
        self._sections.append(
            self._pipeline.render(widget, context=context, renderer_code=renderer_code)
        )
        return self

    def reset(self) -> Self:
        """Clear every accumulated section (``report_code`` and the
        composed pipeline are the builder's construction-time
        identity, not accumulated steps), per
        ``core.BaseBuilder.reset()``'s own contract."""
        self._sections = []
        return self

    def build(self) -> Report:
        """Assemble the final ``Report`` from the sections rendered so
        far, carrying every section warning forward."""
        return Report(
            report_code=self._report_code,
            generated_at=datetime.now(timezone.utc),
            sections=tuple(self._sections),
            warnings=tuple(warning for section in self._sections for warning in section.warnings),
        )
