"""``Report``: a durable, point-in-time generated document composed
of already-rendered sections (design spec §13).

Deliberately a ``BaseValueObject``, not a ``BaseEntity`` -- an
immutable, produced-once artifact exactly like
``optimization.OptimizationResult``/``agents.AgentResult``, never a
long-lived configuration a user edits in place the way a ``Dashboard``
(§10) is. No ``ReportRepository`` exists, for the same reason no
result-repository exists one and two layers down: a Result-shaped
output is handed back to its caller, never independently persisted by
this package (§13, §22).
"""

from __future__ import annotations

import dataclasses
from datetime import datetime

from mineproductivity.core import BaseValueObject

from mineproductivity.visualization.renderer import RenderedOutput

__all__ = ["Report"]


@dataclasses.dataclass(frozen=True, slots=True)
class Report(BaseValueObject):
    """An ordered set of fully-rendered sections as one exportable
    artifact -- ``sections`` are ``RenderedOutput``\\ s, never raw
    ``PresentationModel``\\ s: a Report is, by definition, the
    finished document a human reads or downloads (design spec §13).

    Examples
    --------
    >>> from datetime import timezone
    >>> report = Report(
    ...     report_code="SHIFT.Handover.2026-07-06",
    ...     generated_at=datetime(2026, 7, 6, tzinfo=timezone.utc),
    ... )
    >>> report.sections
    ()
    """

    report_code: str
    generated_at: datetime
    sections: tuple[RenderedOutput, ...] = dataclasses.field(default=(), kw_only=True)
    warnings: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
