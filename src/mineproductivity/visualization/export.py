"""``ExportRequest``/``ExportResult``: converting a rendered artifact
into a downloadable form (design spec §18).

``Export`` is deliberately NOT a reuse of ``connectors``, despite both
moving structured data across a system boundary: a connector reads an
external vendor system *into* the platform (spec 04 §3); Export
writes an already-rendered artifact *out of* the platform, in the
opposite direction -- the two share no code (§18, §32's recorded
anti-pattern). Exporting is not a third registrable concept: an
export is simply one more ``RenderingPipeline.render`` (§11) call
targeting a file-producing ``Renderer``, wrapped in an
``ExportResult`` rather than displayed live -- this package
introduces no separate export-execution mechanism.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any

from mineproductivity.core import BaseValueObject

from mineproductivity.visualization.report import Report

__all__ = ["ExportRequest", "ExportResult"]


@dataclasses.dataclass(frozen=True, slots=True)
class ExportRequest(BaseValueObject):
    """A request to convert a ``Dashboard``'s current rendering or an
    already-built ``Report`` into a single downloadable artifact
    (design spec §18).

    Examples
    --------
    >>> ExportRequest(renderer_code="PDF.Standard", dashboard_id="DASH-1").renderer_code
    'PDF.Standard'
    """

    renderer_code: str
    dashboard_id: str | None = dataclasses.field(default=None, kw_only=True)
    report: Report | None = dataclasses.field(default=None, kw_only=True)


@dataclasses.dataclass(frozen=True, slots=True)
class ExportResult(BaseValueObject):
    """The outcome of one export request (design spec §18).

    Examples
    --------
    >>> from datetime import timezone
    >>> ExportResult(
    ...     format="pdf", payload=b"%PDF",
    ...     exported_at=datetime(2026, 7, 6, tzinfo=timezone.utc),
    ... ).format
    'pdf'
    """

    format: str
    payload: Any
    exported_at: datetime
